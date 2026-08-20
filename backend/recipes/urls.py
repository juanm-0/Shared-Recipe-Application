from django.urls import path

from .viewsets import IngredientListView, TagListView

urlpatterns = [
    path("tags/", TagListView.as_view(), name="tag-list"),
    path("ingredients/", IngredientListView.as_view(), name="ingredient-list"),
]
