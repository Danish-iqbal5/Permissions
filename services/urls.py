
from django.urls import path
from .views import ProductListView, VendorProductListCreateView, VendorProductDetailView as GenericVendorProductDetailView , VendorProductsView, CartView, VendorProductDetailView

urlpatterns = [
    path('vendor/<uuid:product_id>/', VendorProductDetailView.as_view(), name='vendor-product-detail'),
    path('cart/', CartView.as_view(), name='cart-view'),
    

    path('products/', ProductListView.as_view(), name='product-list-generic'),
    path('vendor/products/', VendorProductListCreateView.as_view(), name='vendor-product-list-create'),
    path('vendor/products/<uuid:id>/', GenericVendorProductDetailView.as_view(), name='vendor-product-detail-generic'),
]
