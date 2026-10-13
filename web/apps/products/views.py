import csv
import io
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from apps.recommendations.service import ai_search, ai_rebuild


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer
    ordering = ['-rating']

    def list(self, request, *args, **kwargs):
        keyword = request.query_params.get('keyword')
        if keyword:
            results = ai_search(keyword, top_k=50)
            # Enrich from DB
            ids = [r.get('id', '') for r in results]
            db_products = Product.objects.select_related('category').filter(id__in=ids)
            db_map = {p.id: ProductSerializer(p).data for p in db_products}
            enriched = [db_map.get(r['id'], r) for r in results if r.get('id') in db_map]
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('pageSize', 20))
            start = (page - 1) * page_size
            return Response({
                'page': page,
                'totalPages': -(-len(enriched) // page_size),
                'data': enriched[start:start + page_size]
            })

        # Standard filter
        qs = self.get_queryset()
        category_id = request.query_params.get('categoryId')
        min_price = request.query_params.get('minPrice')
        max_price = request.query_params.get('maxPrice')
        if category_id:
            qs = qs.filter(category_id=category_id)
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser])
    def import_csv(self, request):
        file = request.FILES.get('file')
        category_id = request.data.get('category_id')
        if not file or not category_id:
            return Response({'error': 'file and category_id required'}, status=400)

        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return Response({'error': 'Category not found'}, status=404)

        decoded = file.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))
        products = []
        for row in reader:
            products.append(Product(
                id=row.get('id', row.get('Id', row.get('product_id', ''))).strip(),
                category=category,
                name=row.get('name', row.get('Name', '')).strip(),
                brand=row.get('brand', row.get('Brand', '')).strip() or None,
                price=float(row.get('price', row.get('Price', 0)) or 0),
                original_price=float(row.get('original_price', row.get('OriginalPrice', 0)) or 0),
                discount_rate=float(row.get('discount', row.get('discount_rate', 0)) or 0),
                rating=float(row.get('rating', row.get('Rating', 0)) or 0),
                review_count=int(row.get('review_count', row.get('ReviewCount', 0)) or 0),
                image_url=row.get('image_url', row.get('ImageUrl', row.get('url', ''))).strip() or None,
            ))

        Product.objects.bulk_create(products, ignore_conflicts=True)
        # Trigger AI rebuild
        ai_rebuild()
        return Response({'message': f'Imported {len(products)} products. AI rebuild triggered.'})

    @action(detail=False, methods=['post'])
    def init_categories(self, request):
        defaults = [
            (1, 'Chăm sóc da mặt', 'Beauty'),
            (2, 'Điện gia dụng', 'Electronics'),
            (3, 'Bách hóa online', 'Grocery'),
            (4, 'Thời trang', 'Fashion'),
        ]
        for cid, name, desc in defaults:
            Category.objects.get_or_create(id=cid, defaults={'name': name, 'description': desc})
        return Response({'categories': list(Category.objects.values('id', 'name'))})
