from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .viewsets import IngredientListView, RecipeViewSet, TagListView

router = DefaultRouter()
router.register("recipes", RecipeViewSet, basename="recipe")

urlpatterns = [
    path("tags/", TagListView.as_view(), name="tag-list"),
    path("ingredients/", IngredientListView.as_view(), name="ingredient-list"),
    path("", include(router.urls)),
]
