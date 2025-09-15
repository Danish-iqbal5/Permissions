from rest_framework import serializers
from .models import Product
from authentication.models import UserProfile
from .models import Cart, CartItem , Product

class ProductSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.full_name', read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'vendor_name', 'retail_price', 'whole_sale_price', 'stock_quantity']

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

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.retail_price', max_digits=10, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    quantity = serializers.IntegerField(min_value=1)

    
    class Meta:
        model = CartItem
        fields = ['id', 'product_name', 'product_price', 'quantity', 'total_price']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)  # This uses the related_name='items'
    total_price = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price']
