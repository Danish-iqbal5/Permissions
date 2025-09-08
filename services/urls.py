
from django.urls import path, include
from .views import ProductsListView


urlpatterns = [
    path('list/', ProductsListView.as_view(), name='products-list'),
]
