from django.db.models import Avg, Count, Prefetch
from rest_framework import mixins, status, viewsets
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Ingredient, Recipe, RecipeIngredient, RecipeTag, Review, Tag
from .serializers import (
    IngredientSerializer,
    RecipeDetailSerializer,
    RecipeListSerializer,
    RecipeWriteSerializer,
    TagSerializer,
)


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


class RecipeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            return RecipeListSerializer
        if self.action in ("create", "update", "partial_update"):
            return RecipeWriteSerializer
        return RecipeDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()
        output_serializer = RecipeDetailSerializer(recipe, context=self.get_serializer_context())
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        queryset = Recipe.objects.annotate(
            average_rating=Avg("reviews__rating"),
            review_count=Count("reviews", distinct=True),
        )

        if self.action == "list":
            queryset = queryset.prefetch_related(
                Prefetch(
                    "recipe_tags",
                    queryset=RecipeTag.objects.select_related("tag").order_by("order"),
                )
            )
        else:
            queryset = queryset.select_related("owner", "original_recipe").prefetch_related(
                Prefetch(
                    "recipe_tags",
                    queryset=RecipeTag.objects.select_related("tag").order_by("order"),
                ),
                Prefetch(
                    "recipe_ingredients",
                    queryset=RecipeIngredient.objects.select_related("ingredient").order_by("order"),
                ),
                Prefetch("reviews", queryset=Review.objects.select_related("user")),
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
