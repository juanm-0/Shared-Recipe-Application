from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ReviewCreateView, ReviewDetailView
from .viewsets import IngredientListView, RecipeViewSet, TagListView

router = DefaultRouter()
router.register("recipes", RecipeViewSet, basename="recipe")

urlpatterns = [
    path("tags/", TagListView.as_view(), name="tag-list"),
    path("ingredients/", IngredientListView.as_view(), name="ingredient-list"),
    path("recipes/<int:recipe_id>/reviews/", ReviewCreateView.as_view(), name="review-create"),
    path("recipes/<int:recipe_id>/reviews/<int:review_id>/", ReviewDetailView.as_view(), name="review-detail"),
    path("", include(router.urls)),
]
