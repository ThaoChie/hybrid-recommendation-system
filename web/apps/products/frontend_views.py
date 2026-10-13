"""Frontend views — render Django templates."""
from django.shortcuts import render, get_object_or_404
from .models import Product, Category
from apps.recommendations.service import ai_search, ai_cross_sell
from apps.tracking.vector_store import get_user_history


def home(request):
    categories = Category.objects.all()
    products = Product.objects.select_related('category').order_by('-rating')[:20]

    # Personalized feed nếu user đã login
    personalized = []
    if request.user.is_authenticated:
        history_ids = get_user_history(str(request.user.id), limit=5)
        if history_ids:
            seen = set(history_ids)
            for pid in history_ids[:3]:
                recs = ai_cross_sell(pid, top_k=5)
                for r in recs:
                    if r.get('id') and r['id'] not in seen:
                        seen.add(r['id'])
                        personalized.append(r)
            personalized = personalized[:10]

    return render(request, 'home.html', {
        'categories': categories,
        'products': products,
        'personalized': personalized,
    })


def search_page(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('categoryId', '')
    results = []

    if query:
        ai_results = ai_search(query, top_k=40)
        for r in ai_results:
            results.append(type('P', (), r)())
    elif category_id:
        qs = Product.objects.select_related('category').filter(category_id=category_id).order_by('-rating')[:40]
        results = list(qs)
    else:
        results = list(Product.objects.select_related('category').order_by('-rating')[:40])

    return render(request, 'search.html', {'query': query, 'results': results})


def product_detail(request, product_id):
    product = get_object_or_404(Product.objects.select_related('category'), id=product_id)
    recs = ai_cross_sell(product_id, top_k=10)
    recommendations = [type('P', (), r)() for r in recs]
    return render(request, 'product_detail.html', {'product': product, 'recommendations': recommendations})
