from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import Recipe

from .serializers import (
    ShoppingListImportSerializer,
    ShoppingListItemCreateSerializer,
    ShoppingListItemSerializer,
    ShoppingListSerializer,
)
from .services import get_or_create_shopping_list, import_recipe_into_shopping_list, with_prefetched_items


class ShoppingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        shopping_list = get_or_create_shopping_list(request.user)
        shopping_list = with_prefetched_items(shopping_list)
        serializer = ShoppingListSerializer(shopping_list)
        return Response(serializer.data)


class ShoppingListItemCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ShoppingListItemCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        output_serializer = ShoppingListItemSerializer(item)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class ShoppingListImportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        input_serializer = ShoppingListImportSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        recipe = get_object_or_404(Recipe, pk=input_serializer.validated_data["recipe_id"])
        shopping_list = import_recipe_into_shopping_list(recipe, request.user)
        shopping_list = with_prefetched_items(shopping_list)
        output_serializer = ShoppingListSerializer(shopping_list)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
