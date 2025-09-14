from rest_framework import serializers
from .models import Product
from Permissions.models import UserProfile

class ProductSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.full_name', read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'vendor', 'vendor_name', 'retail_price', 'whole_sale_price', 'stock_quantity']

class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'retail_price', 'whole_sale_price', 'stock_quantity']
    
    def validate(self, data):
        if data['whole_sale_price'] >= data['retail_price']:
            raise serializers.ValidationError("Wholesale price must be less than retail price")
        if data['stock_quantity'] < 0:
            raise serializers.ValidationError("Stock quantity cannot be negative")
        return data

