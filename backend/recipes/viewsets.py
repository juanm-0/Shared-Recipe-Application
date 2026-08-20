from django.db.models import Avg, Count, Prefetch
from rest_framework import mixins, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly

from .models import Ingredient, Recipe, RecipeTag, Tag
from .serializers import IngredientSerializer, RecipeListSerializer, TagSerializer


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


SORT_FIELDS = {
    "name": "name",
    "-name": "-name",
    "rating": "average_rating",
    "-rating": "-average_rating",
    "created_at": "created_at",
    "-created_at": "-created_at",
}


class RecipeViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        return RecipeListSerializer

    def get_queryset(self):
        queryset = Recipe.objects.annotate(
            average_rating=Avg("reviews__rating"),
            review_count=Count("reviews", distinct=True),
        ).prefetch_related(
            Prefetch(
                "recipe_tags",
                queryset=RecipeTag.objects.select_related("tag").order_by("order"),
            )
        )

        params = self.request.query_params

        tag = params.get("tag")
        if tag:
            queryset = queryset.filter(recipe_tags__tag_id=tag)

        ingredient = params.get("ingredient")
        if ingredient:
            queryset = queryset.filter(recipe_ingredients__ingredient_id=ingredient)

        owner = params.get("owner")
        if owner:
            queryset = queryset.filter(owner_id=owner)

        min_rating = params.get("min_rating")
        if min_rating:
            queryset = queryset.filter(average_rating__gte=min_rating)

        sort = params.get("sort", "-created_at")
        queryset = queryset.order_by(SORT_FIELDS.get(sort, "-created_at"))

        return queryset
