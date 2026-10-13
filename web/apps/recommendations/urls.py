from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search),
    path('cross-sell/<str:product_id>/', views.cross_sell),
    path('personalized/', views.personalized_feed),
    path('metrics/', views.metrics),
    path('rebuild/', views.rebuild),
    path('health/', views.health),
]
