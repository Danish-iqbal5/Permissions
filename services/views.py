from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Product, Cart, CartItem 
from .serializers import ProductSerializer, ProductCreateSerializer, CartItemSerializer, CartSerializer
from authentication.models import User
from rest_framework import generics, status
from django.shortcuts import get_object_or_404
from authentication.permissions import IsVendor
from django.core.cache import cache
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from Notifications.models import Notification



class VendorProductsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            if user.user_type != 'vendor' or not user.is_fully_active():
                return Response({"error": "Vendor access required"}, status=403)
        except:
            return Response({"error": "User profile not found"}, status=404)
        
        products = Product.objects.filter(vendor=user)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        try:
            user = request.user
            if user.user_type != 'vendor' or not user.is_fully_active():
                return Response({"error": "Vendor access required"}, status=403)
        except:
            return Response({"error": "User profile not found"}, status=404)
        
        serializer = ProductCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(vendor=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VendorProductDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self, request, product_id):
        try:
            user = request.user
            if user.user_type != 'vendor' or not user.is_fully_active():
                return None, Response({"error": "Vendor access required"}, status=403)
            
            product = Product.objects.get(id=product_id, vendor=user)
            return product, None
        except Product.DoesNotExist:
            return None, Response({"error": "Product not found"}, status=404)
        except:
            return None, Response({"error": "User profile not found"}, status=404)
    
    def get(self, request, product_id):
        product, error_response = self.get_object(request, product_id)
        if error_response:
            return error_response
        
        serializer = ProductSerializer(product)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, product_id):
        product, error_response = self.get_object(request, product_id)
        if error_response:
            return error_response
        
        serializer = ProductCreateSerializer(product, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, product_id):
        product, error_response = self.get_object(request, product_id)
        if error_response:
            return error_response
        
        
        product.is_active = False
        product.save()
        return Response({"message": "Product deactivated successfully"}, status=status.HTTP_200_OK)


class CartView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_user_profile(self, request):
        try:
            user = request.user
            if user.user_type not in ['normal_customer', 'vip_customer'] or not user.is_fully_active():
                return None, Response({"error": "Customer access required"}, status=403)
            return user, None
        except:
            return None, Response({"error": "User profile not found"}, status=404)
    
    def get(self, request):
        user, error_response = self.get_user_profile(request)
        if error_response:
            return error_response
        
        cart, created = Cart.objects.get_or_create(user=user)
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        
        user, error_response = self.get_user_profile(request)
        if error_response:
            return error_response
        
        cart, created = Cart.objects.get_or_create(user=user)
        
        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            quantity = serializer.validated_data['quantity']
            
            try:
                product = Product.objects.get(id=product_id, is_active=True)
                
        
                if product.stock_quantity < quantity:
                    return Response({"error": "Insufficient stock"}, status=400)
                
                
                cart_item, item_created = CartItem.objects.get_or_create(
                    cart=cart, 
                    product=product,
                    defaults={'quantity': quantity}
                )
                
                if not item_created:
                    
                    new_quantity = cart_item.quantity + quantity
                    if product.stock_quantity < new_quantity:
                        return Response({
                            "error": f"Cannot add {quantity} more. Only {product.stock_quantity - cart_item.quantity} available"
                        }, status=400)
                    cart_item.quantity = new_quantity
                    cart_item.save()
                
                return Response(CartItemSerializer(cart_item).data, status=status.HTTP_201_CREATED)
                
            except Product.DoesNotExist:
                return Response({"error": "Product not found"}, status=404)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






# class ProductListView(generics.ListAPIView):
   
#     queryset = Product.objects.filter(is_active=True, stock_quantity__gt=0)
#     serializer_class = ProductSerializer
#     permission_classes = []

class ProductListView(APIView):
    permission_classes = []

    def get(self, request):
        cached_data = cache.get("product_list")
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)

        products = Product.objects.filter(is_active=True, stock_quantity__gt=0)
        serializer = ProductSerializer(products, many=True)
        cache.set("product_list", serializer.data, timeout=300)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VendorProductListCreateView(generics.ListCreateAPIView):
   
    serializer_class = ProductSerializer
    permission_classes = [IsVendor]
    
    def get_queryset(self):
    
        return Product.objects.filter(vendor=self.request.user)
    
    def get_serializer_class(self):
       
        if self.request.method == 'POST':
            return ProductCreateSerializer
        return ProductSerializer
    
    def perform_create(self, serializer):
        
        serializer.save(vendor=self.request.user)


class VendorProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    
    serializer_class = ProductCreateSerializer
    permission_classes = [IsVendor]
    lookup_field = 'id'
    
    def get_queryset(self):
    
        return Product.objects.filter(vendor=self.request.user)
    
    def get_serializer_class(self):
        
        if self.request.method == 'GET':
            return ProductSerializer
        return ProductCreateSerializer
    
    def perform_destroy(self, instance):
       
        instance.is_active = False
        instance.save()
    
    def destroy(self, request, *args, **kwargs):
    # Get the product instance to be deleted
     instance = self.get_object()
    
    # Perform the deletion
     instance.delete()  # This deletes the object from the database entirely
    
     return Response(
        {"message": "Product deleted successfully"}, 
        status=status.HTTP_204_NO_CONTENT  # HTTP 204 No Content for successful deletion
    )






def send_notification_to_user(user_id, message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "notify",
            "message": message,
        }
    )