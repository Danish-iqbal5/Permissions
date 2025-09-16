from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Product, Cart, CartItem 
from .serializers import ProductSerializer, ProductCreateSerializer, CartItemSerializer, CartSerializer
from authentication.models import User

class ProductsListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        products = Product.objects.filter(is_active=True, stock_quantity__gt=0)
        serializer = ProductSerializer(products, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class VendorProductsView(APIView):
    """Vendor product management"""
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
    """Individual product management for vendors"""
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
        
        # Soft delete - just mark as inactive
        product.is_active = False
        product.save()
        return Response({"message": "Product deactivated successfully"}, status=status.HTTP_200_OK)


class CartView(APIView):
    """Shopping cart management"""
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
        """Add item to cart"""
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
                
                # Check stock
                if product.stock_quantity < quantity:
                    return Response({"error": "Insufficient stock"}, status=400)
                
                # Get or create cart item
                cart_item, item_created = CartItem.objects.get_or_create(
                    cart=cart, 
                    product=product,
                    defaults={'quantity': quantity}
                )
                
                if not item_created:
                    # Update quantity if item already exists
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
