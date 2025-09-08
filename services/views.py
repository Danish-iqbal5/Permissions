from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

class ProductsListView(APIView):
    permission_classes = [AllowAny]
    def get(self , request):
         # Sample product data
        return Response("Products List")