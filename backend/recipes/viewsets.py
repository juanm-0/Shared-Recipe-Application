from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import Ingredient, Tag
from .serializers import IngredientSerializer, TagSerializer


class TagListView(ListAPIView):
    queryset = Tag.objects.order_by("name")
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientListView(ListAPIView):
    queryset = Ingredient.objects.order_by("name")
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None
