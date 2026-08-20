from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from recipes.models import Ingredient, RecipeIngredient, Tag

pytestmark = pytest.mark.django_db


def test_list_tags_is_public_and_unpaginated():
    Tag.objects.create(name="Vegan")
    Tag.objects.create(name="Quick")
    client = APIClient()
    response = client.get("/api/tags/")
    assert response.status_code == 200
    assert isinstance(response.data, list)
    assert len(response.data) == 2


def test_list_ingredients_is_public_and_unpaginated():
    Ingredient.objects.create(name="Flour")
    client = APIClient()
    response = client.get("/api/ingredients/")
    assert response.status_code == 200
    assert isinstance(response.data, list)
    assert len(response.data) == 1


from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext

from recipes.models import Recipe, RecipeTag, Review

User = get_user_model()


def _make_recipe(owner, name="Soup", tags=None):
    recipe = Recipe.objects.create(name=name, steps=["Boil"], owner=owner)
    for i, tag in enumerate(tags or []):
        RecipeTag.objects.create(recipe=recipe, tag=tag, order=i)
    return recipe


def test_recipe_list_returns_public_grid_payload():
    owner = User.objects.create_user(username="chef1", password="pw12345")
    _make_recipe(owner, name="Soup")
    client = APIClient()
    response = client.get("/api/recipes/")
    assert response.status_code == 200
    assert response.data["count"] == 1
    result = response.data["results"][0]
    assert set(result.keys()) == {"id", "name", "image", "average_rating", "review_count", "tags"}


def test_recipe_list_filters_by_tag():
    owner = User.objects.create_user(username="chef2", password="pw12345")
    vegan = Tag.objects.create(name="Vegan")
    quick = Tag.objects.create(name="Quick")
    match = _make_recipe(owner, name="Salad", tags=[vegan])
    _make_recipe(owner, name="Steak", tags=[quick])
    client = APIClient()
    response = client.get(f"/api/recipes/?tag={vegan.id}")
    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == match.id


def test_recipe_list_filters_by_min_rating():
    owner = User.objects.create_user(username="chef3", password="pw12345")
    reviewer = User.objects.create_user(username="reviewer3", password="pw12345")
    high = _make_recipe(owner, name="Great Soup")
    low = _make_recipe(owner, name="Meh Soup")
    Review.objects.create(recipe=high, user=reviewer, rating=5, comment="Great")
    Review.objects.create(recipe=low, user=reviewer, rating=2, comment="Meh")
    client = APIClient()
    response = client.get("/api/recipes/?min_rating=4")
    assert response.status_code == 200
    ids = [r["id"] for r in response.data["results"]]
    assert ids == [high.id]


def test_recipe_list_sort_by_name():
    owner = User.objects.create_user(username="chef4", password="pw12345")
    _make_recipe(owner, name="Zebra Stew")
    _make_recipe(owner, name="Apple Pie")
    client = APIClient()
    response = client.get("/api/recipes/?sort=name")
    names = [r["name"] for r in response.data["results"]]
    assert names == ["Apple Pie", "Zebra Stew"]


def test_recipe_list_query_count_stays_flat_as_dataset_grows():
    owner = User.objects.create_user(username="chef5", password="pw12345")
    tag = Tag.objects.create(name="Tag5")
    client = APIClient()

    _make_recipe(owner, name="Solo Recipe", tags=[tag])
    with CaptureQueriesContext(connection) as one_recipe_queries:
        client.get("/api/recipes/")

    for i in range(10):
        _make_recipe(owner, name=f"Recipe {i}", tags=[tag])

    with CaptureQueriesContext(connection) as many_recipe_queries:
        response = client.get("/api/recipes/")

    assert response.status_code == 200
    assert response.data["count"] == 11
    assert len(many_recipe_queries.captured_queries) == len(one_recipe_queries.captured_queries)


def test_recipe_detail_returns_full_payload():
    owner = User.objects.create_user(username="chef6", password="pw12345")
    flour = Ingredient.objects.create(name="Flour6")
    tag = Tag.objects.create(name="Tag6")
    recipe = Recipe.objects.create(name="Bread", steps=["Mix", "Bake"], owner=owner)
    RecipeIngredient.objects.create(
        recipe=recipe, ingredient=flour, amount=Decimal("2"), unit="cup", order=1
    )
    RecipeTag.objects.create(recipe=recipe, tag=tag, order=1)

    client = APIClient()
    response = client.get(f"/api/recipes/{recipe.id}/")
    assert response.status_code == 200
    assert response.data["name"] == "Bread"
    assert response.data["ingredients"][0]["ingredient_name"] == "Flour6"
    assert response.data["tags"][0]["name"] == "Tag6"
    assert response.data["owner"] == "chef6"
    assert response.data["can_edit"] is False


def test_recipe_detail_can_edit_true_for_owner():
    owner = User.objects.create_user(username="chef7", password="pw12345")
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)

    client = APIClient()
    client.force_authenticate(user=owner)
    response = client.get(f"/api/recipes/{recipe.id}/")
    assert response.status_code == 200
    assert response.data["can_edit"] is True


def test_recipe_detail_not_found_returns_404():
    client = APIClient()
    response = client.get("/api/recipes/999999/")
    assert response.status_code == 404
    assert response.data["code"] == "not_found"


def test_recipe_create_happy_path():
    owner = User.objects.create_user(username="chef8", password="pw12345")
    client = APIClient()
    client.force_authenticate(user=owner)
    payload = {
        "name": "Pancakes",
        "steps": ["Mix", "Cook"],
        "ingredients": [{"ingredient_name": "Flour", "amount": "1.5", "unit": "cup"}],
        "tags": ["Breakfast", "Quick"],
    }
    response = client.post("/api/recipes/", payload, format="json")
    assert response.status_code == 201
    assert response.data["name"] == "Pancakes"
    assert response.data["ingredients"][0]["ingredient_name"] == "Flour"
    assert [t["name"] for t in response.data["tags"]] == ["Breakfast", "Quick"]
    assert response.data["can_edit"] is True


def test_recipe_create_reuses_existing_tag_case_insensitively():
    owner = User.objects.create_user(username="chef9", password="pw12345")
    Tag.objects.create(name="Vegan")
    client = APIClient()
    client.force_authenticate(user=owner)
    payload = {
        "name": "Salad",
        "steps": ["Toss"],
        "ingredients": [{"ingredient_name": "Lettuce", "amount": "1", "unit": "whole"}],
        "tags": ["vegan"],
    }
    response = client.post("/api/recipes/", payload, format="json")
    assert response.status_code == 201
    assert Tag.objects.count() == 1


def test_recipe_create_rejects_more_than_five_tags():
    owner = User.objects.create_user(username="chef10", password="pw12345")
    client = APIClient()
    client.force_authenticate(user=owner)
    payload = {
        "name": "Curry",
        "steps": ["Simmer"],
        "ingredients": [{"ingredient_name": "Rice", "amount": "1", "unit": "cup"}],
        "tags": ["a", "b", "c", "d", "e", "f"],
    }
    response = client.post("/api/recipes/", payload, format="json")
    assert response.status_code == 400
    assert response.data["code"] == "tag_limit_exceeded"


def test_recipe_create_rejects_empty_ingredients():
    owner = User.objects.create_user(username="chef11", password="pw12345")
    client = APIClient()
    client.force_authenticate(user=owner)
    payload = {"name": "Empty", "steps": ["Do nothing"], "ingredients": []}
    response = client.post("/api/recipes/", payload, format="json")
    assert response.status_code == 400
    assert response.data["code"] == "validation_error"


def test_recipe_create_rejects_duplicate_ingredient_in_one_payload():
    owner = User.objects.create_user(username="chef11b", password="pw12345")
    client = APIClient()
    client.force_authenticate(user=owner)
    payload = {
        "name": "Double Flour",
        "steps": ["Mix"],
        "ingredients": [
            {"ingredient_name": "Flour11b", "amount": "1", "unit": "cup"},
            {"ingredient_name": "Flour11b", "amount": "2", "unit": "cup"},
        ],
    }
    response = client.post("/api/recipes/", payload, format="json")
    assert response.status_code == 400
    assert response.data["code"] == "validation_error"


def test_recipe_create_requires_authentication():
    client = APIClient()
    payload = {
        "name": "Nope",
        "steps": ["x"],
        "ingredients": [{"ingredient_name": "x", "amount": "1", "unit": "whole"}],
    }
    response = client.post("/api/recipes/", payload, format="json")
    assert response.status_code == 401
