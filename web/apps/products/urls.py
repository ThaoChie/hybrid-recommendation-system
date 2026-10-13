from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet

router = DefaultRouter()
router.register('', ProductViewSet, basename='products')

urlpatterns = [
    path('categories/', CategoryViewSet.as_view({'get': 'list'})),
    path('', include(router.urls)),
]
