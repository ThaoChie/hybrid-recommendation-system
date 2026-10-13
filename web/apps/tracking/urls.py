from django.urls import path
from . import views

urlpatterns = [
    path('interaction/', views.log_interaction),
    path('checkout/', views.log_checkout),
]
