from django.db import models, transaction
from django.db.models import Avg, Count, Subquery, Value
from django.db.models.functions import Coalesce

from .models import Recipe, RecipeIngredient, RecipeTag, Review


def copy_recipe(original_recipe, new_owner):
    with transaction.atomic():
        new_recipe = Recipe.objects.create(
            name=original_recipe.name,
            steps=list(original_recipe.steps),
            image=original_recipe.image.name,
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


def recompute_rating_aggregate(recipe_id):
    """Recompute recipe avg_rating/review_count in a single UPDATE.

    Single UPDATE ... WHERE id=x version to avoid a failure where 
    two reviews are written at the same time for a recipe
    """
    reviews_for_recipe = Review.objects.filter(recipe_id=recipe_id)
    avg_subquery = reviews_for_recipe.values("recipe_id").annotate(v=Avg("rating")).values("v")
    count_subquery = reviews_for_recipe.values("recipe_id").annotate(v=Count("id")).values("v")

    Recipe.objects.filter(pk=recipe_id).update(
        avg_rating=Subquery(avg_subquery),
        review_count=Coalesce(
            Subquery(count_subquery, output_field=models.PositiveIntegerField()),
            Value(0),
        ),
    )
