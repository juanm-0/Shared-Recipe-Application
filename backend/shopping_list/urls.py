from django.urls import path

from .views import ShoppingListImportView, ShoppingListItemCreateView, ShoppingListItemDetailView, ShoppingListView

urlpatterns = [
    path("shopping-list/", ShoppingListView.as_view(), name="shopping-list"),
    path("shopping-list/items/", ShoppingListItemCreateView.as_view(), name="shopping-list-item-create"),
    path("shopping-list/items/<int:item_id>/", ShoppingListItemDetailView.as_view(), name="shopping-list-item-detail"),
    path("shopping-list/import/", ShoppingListImportView.as_view(), name="shopping-list-import"),
]
