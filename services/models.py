from django.db import models
from Permissions.models import UserProfile
import uuid

# Create your models here.
class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    vendor = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='products')
    retail_price = models.DecimalField(max_digits=10, decimal_places=2)
    whole_sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField()

    def __str__(self):
        return self.name