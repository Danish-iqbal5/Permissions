from django.contrib import admin
from .models import Product, Cart, CartItem


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'vendor', 'retail_price', 'whole_sale_price', 'stock_quantity', 'is_active', 'created_at')
    list_filter = ('is_active', 'vendor__user_type', 'created_at')
    search_fields = ('name', 'vendor__email', 'vendor__full_name', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Product Information', {
            'fields': ('name', 'description', 'vendor')
        }),
        ('Pricing', {
            'fields': ('retail_price', 'whole_sale_price')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('vendor')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_items', 'total_price', 'created_at', 'updated_at')
    list_filter = ('user__user_type', 'created_at')
    search_fields = ('user__email', 'user__full_name')
    readonly_fields = ('created_at', 'updated_at', 'total_items', 'total_price')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items__product')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart_user', 'product', 'quantity', 'unit_price', 'total_price')
    list_filter = ('cart__user__user_type', 'product__vendor')
    search_fields = ('cart__user__email', 'product__name', 'cart__user__full_name')
    readonly_fields = ('total_price', 'unit_price')
    
    def cart_user(self, obj):
        return obj.cart.user.email
    cart_user.short_description = 'User'
    
    def unit_price(self, obj):
        return obj.product.get_price_for_user(obj.cart.user)
    unit_price.short_description = 'Unit Price'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cart__user', 'product', 'product__vendor')
