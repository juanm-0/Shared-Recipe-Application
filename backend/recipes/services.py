from django.db import transaction

from .models import Recipe, RecipeIngredient, RecipeTag


def copy_recipe(original_recipe, new_owner):
    with transaction.atomic():
        new_recipe = Recipe.objects.create(
            name=original_recipe.name,
            steps=original_recipe.steps,
            image=original_recipe.image,
            owner=new_owner,
            original_recipe=original_recipe,
            original_owner=original_recipe.owner,
        )
        for ri in original_recipe.recipe_ingredients.all():
            RecipeIngredient.objects.create(
                recipe=new_recipe,
                ingredient=ri.ingredient,
                amount=ri.amount,
                unit=ri.unit,
                order=ri.order,
            )
        for rt in original_recipe.recipe_tags.all():
            RecipeTag.objects.create(recipe=new_recipe, tag=rt.tag, order=rt.order)
    return new_recipe
