import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model

from recipes.models import Ingredient, Recipe, RecipeIngredient, RecipeTag, Review, Tag
from recipes.services import copy_recipe

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_copy_recipe_duplicates_name_steps_and_owner():
    original_owner = User.objects.create_user(username="owner1", password="pw12345")
    copier = User.objects.create_user(username="copier1", password="pw12345")
    original = Recipe.objects.create(name="Soup", steps=["Boil", "Serve"], owner=original_owner)

    copy = copy_recipe(original, copier)

    assert copy.pk != original.pk
    assert copy.name == "Soup"
    assert copy.steps == ["Boil", "Serve"]
    assert copy.owner == copier
    assert copy.original_recipe == original
    assert copy.original_owner == original_owner


def test_copy_recipe_duplicates_ingredients_as_new_rows():
    original_owner = User.objects.create_user(username="owner2", password="pw12345")
    copier = User.objects.create_user(username="copier2", password="pw12345")
    flour = Ingredient.objects.create(name="Flour2")
    original = Recipe.objects.create(name="Bread", steps=["Mix"], owner=original_owner)
    RecipeIngredient.objects.create(
        recipe=original, ingredient=flour, amount=Decimal("2"), unit="cup", order=0
    )

    copy = copy_recipe(original, copier)

    copy_ingredients = list(copy.recipe_ingredients.all())
    assert len(copy_ingredients) == 1
    copy_ri = copy_ingredients[0]
    assert copy_ri.ingredient == flour
    assert copy_ri.amount == Decimal("2")
    assert copy_ri.unit == "cup"
    assert copy_ri.order == 0
    assert copy_ri.pk != original.recipe_ingredients.first().pk


def test_copy_recipe_duplicates_tags_as_new_rows():
    original_owner = User.objects.create_user(username="owner3", password="pw12345")
    copier = User.objects.create_user(username="copier3", password="pw12345")
    tag = Tag.objects.create(name="Tag3")
    original = Recipe.objects.create(name="Curry", steps=["Simmer"], owner=original_owner)
    RecipeTag.objects.create(recipe=original, tag=tag, order=0)

    copy = copy_recipe(original, copier)

    copy_tags = list(copy.recipe_tags.all())
    assert len(copy_tags) == 1
    assert copy_tags[0].tag == tag
    assert copy_tags[0].pk != original.recipe_tags.first().pk


def test_copy_recipe_has_zero_reviews():
    original_owner = User.objects.create_user(username="owner4", password="pw12345")
    reviewer = User.objects.create_user(username="reviewer4", password="pw12345")
    copier = User.objects.create_user(username="copier4", password="pw12345")
    original = Recipe.objects.create(name="Salad", steps=["Toss"], owner=original_owner)
    Review.objects.create(recipe=original, user=reviewer, rating=5, comment="Great")

    copy = copy_recipe(original, copier)

    assert copy.reviews.count() == 0


def test_copy_recipe_editing_copy_ingredients_does_not_affect_original():
    original_owner = User.objects.create_user(username="owner5", password="pw12345")
    copier = User.objects.create_user(username="copier5", password="pw12345")
    flour = Ingredient.objects.create(name="Flour5")
    original = Recipe.objects.create(name="Pancakes", steps=["Mix"], owner=original_owner)
    RecipeIngredient.objects.create(
        recipe=original, ingredient=flour, amount=Decimal("1"), unit="cup", order=0
    )

    copy = copy_recipe(original, copier)
    copy_ri = copy.recipe_ingredients.first()
    copy_ri.amount = Decimal("99")
    copy_ri.save()

    original_ri = original.recipe_ingredients.first()
    assert original_ri.amount == Decimal("1")
