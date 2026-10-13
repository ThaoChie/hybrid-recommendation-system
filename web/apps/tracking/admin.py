from django.contrib import admin
from .models import UserInteraction

@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    list_display = ['user', 'product_id', 'interaction_type', 'created_at']
    list_filter = ['interaction_type']
