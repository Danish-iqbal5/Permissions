from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Product
from .serializers import ProductSerializer, ProductCreateSerializer
from Permissions.models import UserProfile

class ProductsListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        products_data = serializer.data
        
        user_type = 'customer'
        if request.user.is_authenticated:
            try:
                profile = request.user.profile
                user_type = profile.user_type
                if not profile.is_fully_active():
                    user_type = 'customer'
            except:
                user_type = 'customer'
        
        for product in products_data:
            if user_type == 'vip_customer':
                product['price'] = product['whole_sale_price']
                product['price_type'] = 'wholesale'
            else:
                product['price'] = product['retail_price']
                product['price_type'] = 'retail'
            
            if user_type not in ['vip_customer', 'vendor']:
                product.pop('whole_sale_price', None)
        
        return Response(products_data, status=status.HTTP_200_OK)

class VendorProductsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        
        try:
            profile = request.user.profile
            if profile.user_type != 'vendor' or not profile.is_fully_active():
                return Response({"error": "Vendor access required"}, status=403)
        except:
            return Response({"error": "User profile not found"}, status=404)
        
        products = Product.objects.filter(vendor=profile)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
    
        try:
            profile = request.user.profile
            if profile.user_type != 'vendor' or not profile.is_fully_active():
                return Response({"error": "Vendor access required"}, status=403)
        except:
            return Response({"error": "User profile not found"}, status=404)
        
        if not request.data.vendorname:
            return Response({"error": "Vendor name is required"}, status=400)
        
        
        serializer = ProductCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(vendor=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VendorProductDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self, request, product_id):
        try:
            profile = request.user.profile
            if profile.user_type != 'vendor' or not profile.is_fully_active():
                return None, Response({"error": "Vendor access required"}, status=403)
            
            product = Product.objects.get(id=product_id, vendor=profile)
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
        
        product.delete()
        return Response({"message": "Product deleted successfully"}, status=status.HTTP_204_NO_CONTENT)