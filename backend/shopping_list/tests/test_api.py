from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from recipes.models import Ingredient, Recipe, RecipeIngredient

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_get_shopping_list_auto_creates_on_first_access():
    user = User.objects.create_user(username="api1", password="pw12345")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.get("/api/shopping-list/")

    assert response.status_code == 200
    assert response.data["items"] == []


def test_get_shopping_list_requires_authentication():
    client = APIClient()
    response = client.get("/api/shopping-list/")
    assert response.status_code == 401


def test_add_item_to_shopping_list():
    user = User.objects.create_user(username="api2", password="pw12345")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        "/api/shopping-list/items/",
        {"ingredient_name": "Flour Api2", "amount": "2", "unit": "cup"},
    )

    assert response.status_code == 201
    assert response.data["ingredient_name"] == "Flour Api2"
    assert Decimal(response.data["amount"]) == Decimal("2")
    assert response.data["unit"] == "cup"
    assert response.data["source_recipe"] is None
    assert Ingredient.objects.filter(name__iexact="Flour Api2").exists()


def test_add_item_reuses_existing_ingredient_case_insensitively():
    user = User.objects.create_user(username="api3", password="pw12345")
    Ingredient.objects.create(name="Flour Api3")
    client = APIClient()
    client.force_authenticate(user=user)

    client.post("/api/shopping-list/items/", {"ingredient_name": "flour api3", "amount": "1", "unit": "cup"})

    assert Ingredient.objects.filter(name__iexact="flour api3").count() == 1


def test_add_item_requires_authentication():
    client = APIClient()
    response = client.post(
        "/api/shopping-list/items/", {"ingredient_name": "Flour Api4", "amount": "2", "unit": "cup"}
    )
    assert response.status_code == 401


def test_add_item_rejects_non_positive_amount():
    user = User.objects.create_user(username="api5", password="pw12345")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        "/api/shopping-list/items/", {"ingredient_name": "Flour Api5", "amount": "0", "unit": "cup"}
    )

    assert response.status_code == 400
    assert response.data["code"] == "validation_error"


def test_import_recipe_into_shopping_list():
    owner = User.objects.create_user(username="api6owner", password="pw12345")
    importer = User.objects.create_user(username="api6importer", password="pw12345")
    flour = Ingredient.objects.create(name="Flour Api6")
    recipe = Recipe.objects.create(name="Bread Api6", steps=["Mix"], owner=owner)
    RecipeIngredient.objects.create(recipe=recipe, ingredient=flour, amount=Decimal("2"), unit="cup", order=0)

    client = APIClient()
    client.force_authenticate(user=importer)
    response = client.post("/api/shopping-list/import/", {"recipe_id": recipe.id})

    assert response.status_code == 200
    assert len(response.data["items"]) == 1
    assert response.data["items"][0]["ingredient_name"] == "Flour Api6"
    assert Decimal(response.data["items"][0]["amount"]) == Decimal("2")


def test_import_recipe_requires_authentication():
    owner = User.objects.create_user(username="api7owner", password="pw12345")
    recipe = Recipe.objects.create(name="Toast Api7", steps=["Toast"], owner=owner)
    client = APIClient()
    response = client.post("/api/shopping-list/import/", {"recipe_id": recipe.id})
    assert response.status_code == 401


def test_import_recipe_404_for_nonexistent_recipe():
    user = User.objects.create_user(username="api8", password="pw12345")
    client = APIClient()
    client.force_authenticate(user=user)
    response = client.post("/api/shopping-list/import/", {"recipe_id": 999999})
    assert response.status_code == 404
    assert response.data["code"] == "not_found"


def test_import_recipe_missing_recipe_id_returns_400():
    user = User.objects.create_user(username="api9", password="pw12345")
    client = APIClient()
    client.force_authenticate(user=user)
    response = client.post("/api/shopping-list/import/", {})
    assert response.status_code == 400
    assert response.data["code"] == "validation_error"


def test_import_recipe_merges_with_existing_manual_item():
    owner = User.objects.create_user(username="api10owner", password="pw12345")
    importer = User.objects.create_user(username="api10importer", password="pw12345")
    flour = Ingredient.objects.create(name="Flour Api10")
    recipe = Recipe.objects.create(name="Bread Api10", steps=["Mix"], owner=owner)
    RecipeIngredient.objects.create(recipe=recipe, ingredient=flour, amount=Decimal("2"), unit="cup", order=0)

    client = APIClient()
    client.force_authenticate(user=importer)
    client.post("/api/shopping-list/items/", {"ingredient_name": "Flour Api10", "amount": "1", "unit": "cup"})

    response = client.post("/api/shopping-list/import/", {"recipe_id": recipe.id})

    assert response.status_code == 200
    assert len(response.data["items"]) == 1
    assert Decimal(response.data["items"][0]["amount"]) == Decimal("3")


def test_shopping_list_items_returned_in_deterministic_order():
    owner = User.objects.create_user(username="api12owner", password="pw12345")
    importer = User.objects.create_user(username="api12importer", password="pw12345")
    zucchini = Ingredient.objects.create(name="Zucchini Api12")
    mango = Ingredient.objects.create(name="Mango Api12")
    recipe = Recipe.objects.create(name="Cake Api12", steps=["Mix", "Bake"], owner=owner)
    RecipeIngredient.objects.create(recipe=recipe, ingredient=zucchini, amount=Decimal("2"), unit="whole", order=0)
    RecipeIngredient.objects.create(recipe=recipe, ingredient=mango, amount=Decimal("2"), unit="whole", order=1)

    client = APIClient()
    client.force_authenticate(user=importer)
    client.post("/api/shopping-list/import/", {"recipe_id": recipe.id})
    client.post("/api/shopping-list/items/", {"ingredient_name": "Apple Api12", "amount": "1", "unit": "cup"})

    list_response = client.get("/api/shopping-list/")
    ingredient_names = [item["ingredient_name"] for item in list_response.data["items"]]
    assert ingredient_names == ["Zucchini Api12", "Mango Api12", "Apple Api12"]


def test_shopping_lists_are_isolated_per_user():
    user_a = User.objects.create_user(username="api11a", password="pw12345")
    user_b = User.objects.create_user(username="api11b", password="pw12345")

    client_a = APIClient()
    client_a.force_authenticate(user=user_a)
    client_a.post("/api/shopping-list/items/", {"ingredient_name": "Flour Api11", "amount": "2", "unit": "cup"})

    client_b = APIClient()
    client_b.force_authenticate(user=user_b)
    client_b.post("/api/shopping-list/items/", {"ingredient_name": "Sugar Api11", "amount": "1", "unit": "cup"})

    response_a = client_a.get("/api/shopping-list/")
    response_b = client_b.get("/api/shopping-list/")

    assert [item["ingredient_name"] for item in response_a.data["items"]] == ["Flour Api11"]
    assert [item["ingredient_name"] for item in response_b.data["items"]] == ["Sugar Api11"]


def test_add_item_rejects_invalid_unit():
    user = User.objects.create_user(username="api13", password="pw12345")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post(
        "/api/shopping-list/items/", {"ingredient_name": "Flour Api13", "amount": "1", "unit": "furlong"}
    )

    assert response.status_code == 400
    assert response.data["code"] == "validation_error"


def test_import_recipe_rejects_non_integer_recipe_id():
    user = User.objects.create_user(username="api14", password="pw12345")
    client = APIClient()
    client.force_authenticate(user=user)

    response = client.post("/api/shopping-list/import/", {"recipe_id": "not-a-number"})

    assert response.status_code == 400
    assert response.data["code"] == "validation_error"


def test_import_recipe_rolls_back_fully_on_mid_import_failure():
    owner = User.objects.create_user(username="api15owner", password="pw12345")
    importer = User.objects.create_user(username="api15importer", password="pw12345")
    flour = Ingredient.objects.create(name="Flour Api15")
    overflow_ingredient = Ingredient.objects.create(name="Overflow Api15")
    recipe = Recipe.objects.create(name="Bread Api15", steps=["Mix"], owner=owner)
    RecipeIngredient.objects.create(recipe=recipe, ingredient=flour, amount=Decimal("1"), unit="cup", order=0)
    RecipeIngredient.objects.create(
        recipe=recipe, ingredient=overflow_ingredient, amount=Decimal("999999.99"), unit="cup", order=1
    )

    client = APIClient()
    client.force_authenticate(user=importer)
    client.post("/api/shopping-list/items/", {"ingredient_name": "Overflow Api15", "amount": "1", "unit": "cup"})

    response = client.post("/api/shopping-list/import/", {"recipe_id": recipe.id})

    assert response.status_code == 400
    list_response = client.get("/api/shopping-list/")
    ingredient_names = [item["ingredient_name"] for item in list_response.data["items"]]
    assert "Flour Api15" not in ingredient_names


def test_add_item_without_csrf_token_is_rejected():
    user = User.objects.create_user(username="api16", password="pw12345")
    client = APIClient(enforce_csrf_checks=True)
    client.login(username="api16", password="pw12345")

    response = client.post(
        "/api/shopping-list/items/", {"ingredient_name": "Flour Api16", "amount": "1", "unit": "cup"}
    )

    assert response.status_code == 403


def test_add_item_manually_twice_merges_via_api():
    user = User.objects.create_user(username="api17", password="pw12345")
    client = APIClient()
    client.force_authenticate(user=user)

    client.post("/api/shopping-list/items/", {"ingredient_name": "Flour Api17", "amount": "2", "unit": "cup"})
    client.post("/api/shopping-list/items/", {"ingredient_name": "Flour Api17", "amount": "3", "unit": "cup"})

    list_response = client.get("/api/shopping-list/")
    items = list_response.data["items"]
    assert len(items) == 1
    assert Decimal(items[0]["amount"]) == Decimal("5")
