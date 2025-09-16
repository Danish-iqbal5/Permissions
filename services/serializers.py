from rest_framework import serializers
from .models import Product, Cart, CartItem
from authentication.models import User

class ProductSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.full_name', read_only=True)
    price = serializers.SerializerMethodField()
    price_type = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'vendor_name', 'retail_price', 
                 'whole_sale_price', 'stock_quantity', 'is_active', 'price', 'price_type']
    
    def get_price(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                return obj.get_price_for_user(request.user)
            except:
                pass
        return obj.retail_price
    
    def get_price_type(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                if request.user.user_type == 'vip_customer':
                    return 'vip_wholesale'
                elif request.user.user_type == 'vendor':
                    return 'wholesale'
            except:
                pass
        return 'retail'

class ProductCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'description', 'retail_price', 'whole_sale_price', 'stock_quantity']
    
    def validate(self, data):
        if data['whole_sale_price'] >= data['retail_price']:
            raise serializers.ValidationError("Wholesale price must be less than retail price")
        if data['stock_quantity'] < 0:
            raise serializers.ValidationError("Stock quantity cannot be negative")
        return data


class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.UUIDField(write_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    unit_price = serializers.SerializerMethodField(read_only=True)
    total_price = serializers.SerializerMethodField(read_only=True)
    stock_available = serializers.IntegerField(source='product.stock_quantity', read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'product_name', 'quantity', 'unit_price', 
                 'total_price', 'stock_available']
    
    def get_unit_price(self, obj):
        return obj.product.get_price_for_user(obj.cart.user)
    
    def get_total_price(self, obj):
        return obj.total_price


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price', 'total_items', 'updated_at']
