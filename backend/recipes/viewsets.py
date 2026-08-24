from django.db.models import F, Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from accounts.permissions import IsOwnerOrStaff
from .models import Ingredient, Recipe, RecipeIngredient, RecipeTag, Review, Tag
from .serializers import (
    IngredientSerializer,
    RecipeDetailSerializer,
    RecipeListSerializer,
    RecipeWriteSerializer,
    TagSerializer,
)
from .services import copy_recipe


def _int_param(params, key):
    raw = params.get(key)
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        raise ValidationError({key: "Must be an integer."})


def _float_param(params, key):
    raw = params.get(key)
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        raise ValidationError({key: "Must be a number."})


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
    "created_at": "created_at",
    "-created_at": "-created_at",
}

UPDATE_ACTIONS = ("update", "partial_update")
OWNER_ONLY_ACTIONS = UPDATE_ACTIONS + ("destroy",)
WRITE_SERIALIZER_ACTIONS = ("create",) + UPDATE_ACTIONS


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action in OWNER_ONLY_ACTIONS:
            return [IsAuthenticatedOrReadOnly(), IsOwnerOrStaff()]
        return [permission() for permission in self.permission_classes]

    def get_serializer_class(self):
        if self.action == "list":
            return RecipeListSerializer
        if self.action in WRITE_SERIALIZER_ACTIONS:
            return RecipeWriteSerializer
        return RecipeDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()
        output_serializer = RecipeDetailSerializer(recipe, context=self.get_serializer_context())
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()
        output_serializer = RecipeDetailSerializer(recipe, context=self.get_serializer_context())
        return Response(output_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def copy(self, request, pk=None):
        original_recipe = self.get_object()
        new_recipe = copy_recipe(original_recipe, request.user)
        output_serializer = RecipeDetailSerializer(new_recipe, context=self.get_serializer_context())
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        if self.action != "list":
            return self._detail_queryset()
        return self._apply_sort(self._apply_filters(self._list_queryset()))

    def _detail_queryset(self):
        return Recipe.objects.select_related("owner", "original_owner").prefetch_related(
            Prefetch(
                "recipe_tags",
                queryset=RecipeTag.objects.select_related("tag").order_by("order"),
            ),
            Prefetch(
                "recipe_ingredients",
                queryset=RecipeIngredient.objects.select_related("ingredient").order_by("order"),
            ),
            Prefetch("reviews", queryset=Review.objects.select_related("user").order_by("-created_at")),
        )

    def _list_queryset(self):
        return Recipe.objects.prefetch_related(
            Prefetch(
                "recipe_tags",
                queryset=RecipeTag.objects.select_related("tag").order_by("order"),
            )
        )

    def _apply_filters(self, queryset):
        params = self.request.query_params

        tag = _int_param(params, "tag")
        if tag is not None:
            queryset = queryset.filter(recipe_tags__tag_id=tag)

        ingredient = _int_param(params, "ingredient")
        if ingredient is not None:
            queryset = queryset.filter(recipe_ingredients__ingredient_id=ingredient)

        owner = _int_param(params, "owner")
        if owner is not None:
            queryset = queryset.filter(owner_id=owner)

        min_rating = _float_param(params, "min_rating")
        if min_rating is not None:
            queryset = queryset.filter(avg_rating__gte=min_rating)

        return queryset

    def _apply_sort(self, queryset):
        sort = self.request.query_params.get("sort", "-created_at")
        if sort == "rating":
            return queryset.order_by(F("avg_rating").asc(nulls_last=True), "-pk")
        if sort == "-rating":
            return queryset.order_by(F("avg_rating").desc(nulls_last=True), "-pk")
        return queryset.order_by(SORT_FIELDS.get(sort, "-created_at"), "-pk")
