from django.db import models
from django.conf import settings


class UserInteraction(models.Model):
    """Lưu lịch sử tương tác: view, search, buy, add_to_cart."""
    TYPES = [('View', 'View'), ('Search', 'Search'), ('Buy', 'Buy'), ('AddToCart', 'AddToCart')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             null=True, blank=True, related_name='interactions')
    session_id = models.CharField(max_length=100, blank=True, db_index=True)
    product_id = models.CharField(max_length=50, db_index=True)  # Không dùng FK để tránh type mismatch
    interaction_type = models.CharField(max_length=20, choices=TYPES)
    interaction_value = models.FloatField(null=True, blank=True)
    search_query = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_interactions'  # Tên mới, tránh conflict với table cũ
