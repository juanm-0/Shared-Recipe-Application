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


def test_copy_recipe_steps_is_independent_object_from_original():
    original_owner = User.objects.create_user(username="owner6", password="pw12345")
    copier = User.objects.create_user(username="copier6", password="pw12345")
    original = Recipe.objects.create(name="Omelette", steps=["Whisk", "Cook"], owner=original_owner)

    copy = copy_recipe(original, copier)

    assert copy.steps is not original.steps
    copy.steps.append("Serve")
    assert original.steps == ["Whisk", "Cook"]


def test_copy_recipe_duplicates_image_by_reference():
    original_owner = User.objects.create_user(username="owner7", password="pw12345")
    copier = User.objects.create_user(username="copier7", password="pw12345")
    original = Recipe.objects.create(
        name="Tacos", steps=["Assemble"], owner=original_owner, image="recipes/tacos.jpg"
    )

    copy = copy_recipe(original, copier)

    assert copy.image.name == "recipes/tacos.jpg"
    assert copy.image is not original.image


def test_copy_recipe_editing_copy_tags_does_not_affect_original():
    original_owner = User.objects.create_user(username="owner8", password="pw12345")
    copier = User.objects.create_user(username="copier8", password="pw12345")
    tag_a = Tag.objects.create(name="Tag8a")
    tag_b = Tag.objects.create(name="Tag8b")
    original = Recipe.objects.create(name="Pizza", steps=["Bake"], owner=original_owner)
    RecipeTag.objects.create(recipe=original, tag=tag_a, order=0)

    copy = copy_recipe(original, copier)
    copy_rt = copy.recipe_tags.first()
    copy_rt.tag = tag_b
    copy_rt.save()

    original_rt = original.recipe_tags.first()
    assert original_rt.tag == tag_a


def test_copy_recipe_does_not_duplicate_catalog_rows_or_mutate_original_relations():
    original_owner = User.objects.create_user(username="owner9", password="pw12345")
    copier = User.objects.create_user(username="copier9", password="pw12345")
    flour = Ingredient.objects.create(name="Flour9")
    tag = Tag.objects.create(name="Tag9")
    original = Recipe.objects.create(name="Muffins", steps=["Bake"], owner=original_owner)
    RecipeIngredient.objects.create(
        recipe=original, ingredient=flour, amount=Decimal("1"), unit="cup", order=0
    )
    RecipeTag.objects.create(recipe=original, tag=tag, order=0)

    ingredient_count_before = Ingredient.objects.count()
    tag_count_before = Tag.objects.count()

    copy_recipe(original, copier)

    assert Ingredient.objects.count() == ingredient_count_before
    assert Tag.objects.count() == tag_count_before
    assert original.recipe_ingredients.count() == 1
    assert original.recipe_tags.count() == 1


def test_copy_recipe_preserves_multi_ingredient_order():
    original_owner = User.objects.create_user(username="owner10", password="pw12345")
    copier = User.objects.create_user(username="copier10", password="pw12345")
    flour = Ingredient.objects.create(name="Flour10")
    sugar = Ingredient.objects.create(name="Sugar10")
    eggs = Ingredient.objects.create(name="Eggs10")
    original = Recipe.objects.create(name="Cake", steps=["Mix", "Bake"], owner=original_owner)
    RecipeIngredient.objects.create(recipe=original, ingredient=eggs, amount=Decimal("2"), unit="whole", order=0)
    RecipeIngredient.objects.create(recipe=original, ingredient=flour, amount=Decimal("2"), unit="cup", order=1)
    RecipeIngredient.objects.create(recipe=original, ingredient=sugar, amount=Decimal("1"), unit="cup", order=2)

    copy = copy_recipe(original, copier)

    copy_ingredients = list(copy.recipe_ingredients.all())
    assert [ri.ingredient.name for ri in copy_ingredients] == ["Eggs10", "Flour10", "Sugar10"]
    assert [ri.order for ri in copy_ingredients] == [0, 1, 2]
