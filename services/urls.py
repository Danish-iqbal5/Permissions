
from django.urls import path
from .views import ProductsListView, VendorProductsView, VendorProductDetailView

urlpatterns = [
    path('list/', ProductsListView.as_view(), name='products-list'),
    path('vendor/', VendorProductsView.as_view(), name='vendor-products'),
    path('vendor/<uuid:product_id>/', VendorProductDetailView.as_view(), name='vendor-product-detail'),
]
