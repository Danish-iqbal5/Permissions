from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Product
from .serializers import ProductSerializer, ProductCreateSerializer
from authentication.permissions import IsVendor


class ProductListView(generics.ListAPIView):
    """List all active products - accessible to everyone"""
    queryset = Product.objects.filter(is_active=True, stock_quantity__gt=0)
    serializer_class = ProductSerializer
    permission_classes = []


class VendorProductListCreateView(generics.ListCreateAPIView):
    """List vendor's products and create new products"""
    serializer_class = ProductSerializer
    permission_classes = [IsVendor]
    
    def get_queryset(self):
        """Filter products by current vendor"""
        return Product.objects.filter(vendor=self.request.user)
    
    def get_serializer_class(self):
        """Use different serializer for create"""
        if self.request.method == 'POST':
            return ProductCreateSerializer
        return ProductSerializer
    
    def perform_create(self, serializer):
        """Set vendor as current user"""
        serializer.save(vendor=self.request.user)


class VendorProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a vendor's product"""
    serializer_class = ProductCreateSerializer
    permission_classes = [IsVendor]
    lookup_field = 'id'
    
    def get_queryset(self):
        """Filter products by current vendor"""
        return Product.objects.filter(vendor=self.request.user)
    
    def get_serializer_class(self):
        """Use ProductSerializer for GET, ProductCreateSerializer for PUT/PATCH"""
        if self.request.method == 'GET':
            return ProductSerializer
        return ProductCreateSerializer
    
    def perform_destroy(self, instance):
        """Soft delete - mark as inactive instead of deleting"""
        instance.is_active = False
        instance.save()
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to return custom message"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Product deactivated successfully"}, 
            status=status.HTTP_200_OK
        )
