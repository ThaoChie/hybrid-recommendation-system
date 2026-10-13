"""
Recommendation API Views.
- search/cross-sell: proxy đến model service
- personalized: dùng ChromaDB history để gợi ý cho user đã login
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .service import ai_search, ai_cross_sell, ai_metrics, ai_rebuild, ai_health
from apps.tracking.vector_store import get_user_history
from apps.products.models import Product
from apps.products.serializers import ProductSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def search(request):
    """GET /api/v1/recommendations/search/?q=...&top_k=20"""
    q = request.query_params.get('q', '')
    if not q:
        return Response({'error': 'q required'}, status=400)
    top_k = int(request.query_params.get('top_k', 20))
    results = ai_search(q, top_k=top_k)
    return Response({'results': results})


@api_view(['GET'])
@permission_classes([AllowAny])
def cross_sell(request, product_id):
    """GET /api/v1/recommendations/cross-sell/<product_id>/"""
    top_k = int(request.query_params.get('top_k', 10))
    results = ai_cross_sell(product_id, top_k=top_k)
    return Response({'results': results})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def personalized_feed(request):
    """
    GET /api/v1/recommendations/personalized/
    Gợi ý dựa trên lịch sử user (ChromaDB).
    Giải quyết cold-start: user login → lấy history → cross-sell từng product đã xem.
    """
    user_id = str(request.user.id)
    top_k = int(request.query_params.get('top_k', 20))

    # Lấy product IDs từ ChromaDB history
    history_product_ids = get_user_history(user_id, limit=10)

    if not history_product_ids:
        # Chưa có history → trả popular products
        popular = Product.objects.select_related('category').order_by('-rating', '-review_count')[:top_k]
        return Response({
            'source': 'popular',
            'results': ProductSerializer(popular, many=True).data
        })

    # Có history → gọi cross-sell cho top 3 products gần nhất
    all_recommendations = []
    seen_ids = set(history_product_ids)  # Không gợi ý lại sản phẩm đã xem

    for pid in history_product_ids[:3]:
        recs = ai_cross_sell(pid, top_k=10)
        for rec in recs:
            rec_id = rec.get('id', '')
            if rec_id and rec_id not in seen_ids:
                seen_ids.add(rec_id)
                all_recommendations.append(rec)

    # Sort by score, limit
    all_recommendations.sort(key=lambda x: x.get('score', 0), reverse=True)

    # Enrich from DB
    rec_ids = [r['id'] for r in all_recommendations[:top_k]]
    db_products = Product.objects.select_related('category').filter(id__in=rec_ids)
    db_map = {p.id: ProductSerializer(p).data for p in db_products}

    enriched = []
    for r in all_recommendations[:top_k]:
        if r['id'] in db_map:
            enriched.append(db_map[r['id']])
        else:
            enriched.append(r)

    return Response({
        'source': 'personalized',
        'based_on': history_product_ids[:3],
        'results': enriched
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def metrics(request):
    return Response(ai_metrics(int(request.query_params.get('k', 5))))


@api_view(['POST'])
@permission_classes([AllowAny])
def rebuild(request):
    success = ai_rebuild()
    return Response({'success': success})


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response(ai_health())
