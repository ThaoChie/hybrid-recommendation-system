from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from apps.products.frontend_views import home, search_page, product_detail


def health(request):
    return JsonResponse({'status': 'healthy', 'version': '2.0.0'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health),
    # Frontend pages
    path('', home, name='home'),
    path('search/', search_page, name='search'),
    path('product/<str:product_id>/', product_detail, name='product-detail'),
    # REST API
    path('api/v1/products/', include('apps.products.urls')),
    path('api/v1/auth/', include('apps.users.urls')),
    path('api/v1/tracking/', include('apps.tracking.urls')),
    path('api/v1/recommendations/', include('apps.recommendations.urls')),
]
