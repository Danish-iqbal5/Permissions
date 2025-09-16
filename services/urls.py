
from django.urls import path
from .views import ProductsListView, VendorProductsView, VendorProductDetailView, CartView
from .generic_views import ProductListView, VendorProductListCreateView, VendorProductDetailView as GenericVendorProductDetailView

urlpatterns = [
    # Original views
    path('list/', ProductsListView.as_view(), name='products-list'),
    path('vendor/', VendorProductsView.as_view(), name='vendor-products'),
    path('vendor/<uuid:product_id>/', VendorProductDetailView.as_view(), name='vendor-product-detail'),
    path('cart/', CartView.as_view(), name='cart-view'),
    
    # Generic views for vendor product management
    path('products/', ProductListView.as_view(), name='product-list-generic'),
    path('vendor/products/', VendorProductListCreateView.as_view(), name='vendor-product-list-create'),
    path('vendor/products/<uuid:id>/', GenericVendorProductDetailView.as_view(), name='vendor-product-detail-generic'),
]
