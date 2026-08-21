from django.db import transaction

from .models import ShoppingList, ShoppingListItem


def get_or_create_shopping_list(user):
    shopping_list, _ = ShoppingList.objects.get_or_create(user=user)
    return shopping_list


def import_recipe_into_shopping_list(recipe, user):
    shopping_list = get_or_create_shopping_list(user)
    with transaction.atomic():
        for ri in recipe.recipe_ingredients.all():
            existing = ShoppingListItem.objects.filter(
                shopping_list=shopping_list, ingredient=ri.ingredient, unit=ri.unit
            ).first()
            if existing is not None:
                existing.amount = existing.amount + ri.amount
                existing.full_clean()
                existing.save()
            else:
                item = ShoppingListItem(
                    shopping_list=shopping_list,
                    ingredient=ri.ingredient,
                    amount=ri.amount,
                    unit=ri.unit,
                    source_recipe=recipe,
                )
                item.full_clean()
                item.save()
    return shopping_list
