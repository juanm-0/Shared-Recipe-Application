from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from recipes.models import Ingredient, Recipe, RecipeIngredient
from shopping_list.models import ShoppingList, ShoppingListItem
from shopping_list.services import get_or_create_shopping_list, import_recipe_into_shopping_list

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_get_or_create_shopping_list_creates_on_first_call():
    user = User.objects.create_user(username="svc1", password="pw12345")
    assert not ShoppingList.objects.filter(user=user).exists()

    shopping_list = get_or_create_shopping_list(user)

    assert ShoppingList.objects.filter(user=user).count() == 1
    assert shopping_list.user == user


def test_get_or_create_shopping_list_returns_same_list_on_second_call():
    user = User.objects.create_user(username="svc2", password="pw12345")
    first = get_or_create_shopping_list(user)
    second = get_or_create_shopping_list(user)
    assert first.pk == second.pk


def test_import_recipe_creates_new_items_with_source_recipe_set():
    owner = User.objects.create_user(username="svc3", password="pw12345")
    flour = Ingredient.objects.create(name="Flour Svc3")
    recipe = Recipe.objects.create(name="Bread Svc3", steps=["Mix"], owner=owner)
    RecipeIngredient.objects.create(recipe=recipe, ingredient=flour, amount=Decimal("2"), unit="cup", order=0)

    shopping_list = import_recipe_into_shopping_list(recipe, owner)

    items = list(shopping_list.items.all())
    assert len(items) == 1
    assert items[0].ingredient == flour
    assert items[0].amount == Decimal("2")
    assert items[0].unit == "cup"
    assert items[0].source_recipe == recipe


def test_import_recipe_merges_matching_ingredient_and_unit_by_summing():
    owner = User.objects.create_user(username="svc4", password="pw12345")
    flour = Ingredient.objects.create(name="Flour Svc4")
    recipe = Recipe.objects.create(name="Bread Svc4", steps=["Mix"], owner=owner)
    RecipeIngredient.objects.create(recipe=recipe, ingredient=flour, amount=Decimal("2"), unit="cup", order=0)

    shopping_list = get_or_create_shopping_list(owner)
    ShoppingListItem.objects.create(
        shopping_list=shopping_list, ingredient=flour, amount=Decimal("1"), unit="cup"
    )

    import_recipe_into_shopping_list(recipe, owner)

    items = list(shopping_list.items.all())
    assert len(items) == 1
    assert items[0].amount == Decimal("3")


def test_import_recipe_does_not_merge_same_ingredient_different_unit():
    owner = User.objects.create_user(username="svc5", password="pw12345")
    flour = Ingredient.objects.create(name="Flour Svc5")
    recipe = Recipe.objects.create(name="Bread Svc5", steps=["Mix"], owner=owner)
    RecipeIngredient.objects.create(recipe=recipe, ingredient=flour, amount=Decimal("2"), unit="cup", order=0)

    shopping_list = get_or_create_shopping_list(owner)
    ShoppingListItem.objects.create(
        shopping_list=shopping_list, ingredient=flour, amount=Decimal("500"), unit="g"
    )

    import_recipe_into_shopping_list(recipe, owner)

    items = list(shopping_list.items.all())
    assert len(items) == 2
    amounts_by_unit = {item.unit: item.amount for item in items}
    assert amounts_by_unit == {"g": Decimal("500"), "cup": Decimal("2")}


def test_import_recipe_with_multiple_ingredients():
    owner = User.objects.create_user(username="svc6", password="pw12345")
    flour = Ingredient.objects.create(name="Flour Svc6")
    sugar = Ingredient.objects.create(name="Sugar Svc6")
    recipe = Recipe.objects.create(name="Cake Svc6", steps=["Mix", "Bake"], owner=owner)
    RecipeIngredient.objects.create(recipe=recipe, ingredient=flour, amount=Decimal("2"), unit="cup", order=0)
    RecipeIngredient.objects.create(recipe=recipe, ingredient=sugar, amount=Decimal("1"), unit="cup", order=1)

    shopping_list = import_recipe_into_shopping_list(recipe, owner)

    assert shopping_list.items.count() == 2
