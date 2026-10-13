from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'Categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', db_column='CategoryId')
    name = models.CharField(max_length=500, db_column='Name')
    clean_name = models.CharField(max_length=500, blank=True, null=True, db_column='CleanName')
    brand = models.CharField(max_length=255, blank=True, null=True, db_column='Brand')
    price = models.DecimalField(max_digits=18, decimal_places=2, default=0, db_column='Price')
    original_price = models.DecimalField(max_digits=18, decimal_places=2, default=0, db_column='OriginalPrice')
    discount_rate = models.FloatField(default=0, db_column='DiscountRate')
    rating = models.FloatField(default=0, db_column='Rating')
    review_count = models.IntegerField(default=0, db_column='ReviewCount')
    image_url = models.URLField(max_length=1000, blank=True, null=True, db_column='ImageUrl')

    class Meta:
        db_table = 'Products'

    def __str__(self):
        return self.name
