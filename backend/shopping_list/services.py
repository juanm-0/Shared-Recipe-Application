from django.db import IntegrityError, transaction
from django.db.models import Prefetch, prefetch_related_objects

from .models import ShoppingList, ShoppingListItem


def get_or_create_shopping_list(user):
    shopping_list, _ = ShoppingList.objects.get_or_create(user=user)
    return shopping_list


def with_prefetched_items(shopping_list):
    prefetch_related_objects(
        [shopping_list], Prefetch("items", queryset=ShoppingListItem.objects.select_related("ingredient"))
    )
    return shopping_list


def merge_or_create_item(shopping_list, ingredient, amount, unit, source_recipe=None):
    existing = ShoppingListItem.objects.filter(
        shopping_list=shopping_list, ingredient=ingredient, unit=unit
    ).first()
    if existing is not None:
        existing.amount = existing.amount + amount
        existing.full_clean()
        existing.save()
        return existing

    item = ShoppingListItem(
        shopping_list=shopping_list,
        ingredient=ingredient,
        amount=amount,
        unit=unit,
        source_recipe=source_recipe,
    )
    item.full_clean(validate_unique=False)
    try:
        with transaction.atomic():
            item.save()
    except IntegrityError:
        existing = ShoppingListItem.objects.get(
            shopping_list=shopping_list, ingredient=ingredient, unit=unit
        )
        existing.amount = existing.amount + amount
        existing.full_clean()
        existing.save()
        return existing
    return item


def import_recipe_into_shopping_list(recipe, user):
    shopping_list = get_or_create_shopping_list(user)
    with transaction.atomic():
        for ri in recipe.recipe_ingredients.select_related("ingredient"):
            merge_or_create_item(shopping_list, ri.ingredient, ri.amount, ri.unit, source_recipe=recipe)
    return shopping_list
