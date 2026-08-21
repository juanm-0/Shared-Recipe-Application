from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from recipes.models import Ingredient, Recipe, RecipeIngredient, RecipeTag, Review, Tag

pytestmark = pytest.mark.django_db

User = get_user_model()


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


def test_average_rating_is_correct_when_tag_filter_is_applied():
    owner = User.objects.create_user(username="chefavg", password="pw12345")
    r1 = User.objects.create_user(username="rev1", password="pw12345")
    r2 = User.objects.create_user(username="rev2", password="pw12345")
    tag = Tag.objects.create(name="TagAvg")
    recipe = _make_recipe(owner, name="Rated", tags=[tag])
    Review.objects.create(recipe=recipe, user=r1, rating=2, comment="")
    Review.objects.create(recipe=recipe, user=r2, rating=4, comment="")
    response = APIClient().get(f"/api/recipes/?tag={tag.id}")
    assert response.data["results"][0]["average_rating"] == 3.0
    assert response.data["results"][0]["review_count"] == 2


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
    assert not Recipe.objects.filter(name="Double Flour").exists()
    assert not RecipeIngredient.objects.filter(ingredient__name="Flour11b").exists()


def test_recipe_create_requires_authentication():
    client = APIClient()
    payload = {
        "name": "Nope",
        "steps": ["x"],
        "ingredients": [{"ingredient_name": "x", "amount": "1", "unit": "whole"}],
    }
    response = client.post("/api/recipes/", payload, format="json")
    assert response.status_code == 401


def test_recipe_update_happy_path():
    owner = User.objects.create_user(username="chef12", password="pw12345")
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)
    flour = Ingredient.objects.create(name="Flour12")
    RecipeIngredient.objects.create(
        recipe=recipe, ingredient=flour, amount=Decimal("1"), unit="cup", order=1
    )

    client = APIClient()
    client.force_authenticate(user=owner)
    payload = {
        "name": "Better Soup",
        "expected_updated_at": recipe.updated_at.isoformat(),
    }
    response = client.patch(f"/api/recipes/{recipe.id}/", payload, format="json")
    assert response.status_code == 200
    assert response.data["name"] == "Better Soup"


def test_recipe_update_rejects_stale_write():
    owner = User.objects.create_user(username="chef13", password="pw12345")
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)

    client = APIClient()
    client.force_authenticate(user=owner)
    response = client.patch(
        f"/api/recipes/{recipe.id}/",
        {"name": "New Name", "expected_updated_at": "2000-01-01T00:00:00Z"},
        format="json",
    )
    assert response.status_code == 409
    assert response.data["code"] == "stale_write"
    assert response.data["current"]["name"] == "Soup"


def test_recipe_update_requires_expected_updated_at():
    owner = User.objects.create_user(username="chef13b", password="pw12345")
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)

    client = APIClient()
    client.force_authenticate(user=owner)
    response = client.patch(f"/api/recipes/{recipe.id}/", {"name": "New Name"}, format="json")
    assert response.status_code == 400


def test_recipe_update_rejects_non_owner():
    owner = User.objects.create_user(username="chef14", password="pw12345")
    other = User.objects.create_user(username="other14", password="pw12345")
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)

    client = APIClient()
    client.force_authenticate(user=other)
    response = client.patch(
        f"/api/recipes/{recipe.id}/",
        {"name": "Hijacked", "expected_updated_at": recipe.updated_at.isoformat()},
        format="json",
    )
    assert response.status_code == 403


def test_recipe_update_replaces_tags_fully():
    owner = User.objects.create_user(username="chef15", password="pw12345")
    old_tag = Tag.objects.create(name="Old15")
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)
    RecipeTag.objects.create(recipe=recipe, tag=old_tag, order=0)

    client = APIClient()
    client.force_authenticate(user=owner)
    response = client.patch(
        f"/api/recipes/{recipe.id}/",
        {"tags": ["New15"], "expected_updated_at": recipe.updated_at.isoformat()},
        format="json",
    )
    assert response.status_code == 200
    assert [t["name"] for t in response.data["tags"]] == ["New15"]
    assert not RecipeTag.objects.filter(tag=old_tag).exists()


def test_recipe_patch_without_tags_or_ingredients_preserves_them():
    owner = User.objects.create_user(username="chef18", password="pw12345")
    tag = Tag.objects.create(name="Tag18")
    ingredient = Ingredient.objects.create(name="Ingredient18")
    recipe = Recipe.objects.create(name="Original", steps=["Step"], owner=owner)
    RecipeTag.objects.create(recipe=recipe, tag=tag, order=0)
    RecipeIngredient.objects.create(
        recipe=recipe, ingredient=ingredient, amount=Decimal("1"), unit="cup", order=0
    )

    client = APIClient()
    client.force_authenticate(user=owner)
    response = client.patch(
        f"/api/recipes/{recipe.id}/",
        {"name": "Renamed", "expected_updated_at": recipe.updated_at.isoformat()},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["name"] == "Renamed"
    assert [t["name"] for t in response.data["tags"]] == ["Tag18"]
    assert response.data["ingredients"][0]["ingredient_name"] == "Ingredient18"


def test_recipe_delete_happy_path():
    owner = User.objects.create_user(username="chef16", password="pw12345")
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)

    client = APIClient()
    client.force_authenticate(user=owner)
    response = client.delete(f"/api/recipes/{recipe.id}/")
    assert response.status_code == 204
    assert not Recipe.objects.filter(id=recipe.id).exists()


def test_recipe_delete_rejects_non_owner():
    owner = User.objects.create_user(username="chef17", password="pw12345")
    other = User.objects.create_user(username="other17", password="pw12345")
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)

    client = APIClient()
    client.force_authenticate(user=other)
    response = client.delete(f"/api/recipes/{recipe.id}/")
    assert response.status_code == 403
    assert Recipe.objects.filter(id=recipe.id).exists()


def test_recipe_detail_exposes_original_owner_when_set():
    owner = User.objects.create_user(username="chefOrigOwner1", password="pw12345")
    copier = User.objects.create_user(username="copierOrigOwner1", password="pw12345")
    original = Recipe.objects.create(name="Original1", steps=["Step"], owner=owner)
    copy = Recipe.objects.create(
        name="Original1",
        steps=["Step"],
        owner=copier,
        original_recipe=original,
        original_owner=owner,
    )

    client = APIClient()
    response = client.get(f"/api/recipes/{copy.id}/")
    assert response.status_code == 200
    assert response.data["original_owner"] == "chefOrigOwner1"


def test_recipe_detail_original_owner_is_null_when_not_a_copy():
    owner = User.objects.create_user(username="chefOrigOwner2", password="pw12345")
    recipe = Recipe.objects.create(name="Plain", steps=["Step"], owner=owner)

    client = APIClient()
    response = client.get(f"/api/recipes/{recipe.id}/")
    assert response.status_code == 200
    assert response.data["original_owner"] is None


def test_recipe_copy_happy_path():
    owner = User.objects.create_user(username="chefCopy1", password="pw12345")
    copier = User.objects.create_user(username="copierCopy1", password="pw12345")
    tag = Tag.objects.create(name="TagCopy1")
    flour = Ingredient.objects.create(name="FlourCopy1")
    original = Recipe.objects.create(name="Waffles", steps=["Mix", "Cook"], owner=owner)
    RecipeIngredient.objects.create(
        recipe=original, ingredient=flour, amount=Decimal("2"), unit="cup", order=0
    )
    RecipeTag.objects.create(recipe=original, tag=tag, order=0)

    client = APIClient()
    client.force_authenticate(user=copier)
    response = client.post(f"/api/recipes/{original.id}/copy/")
    assert response.status_code == 201
    assert response.data["name"] == "Waffles"
    assert response.data["id"] != original.id
    assert response.data["original_recipe"] == original.id
    assert response.data["original_owner"] == "chefCopy1"
    assert response.data["ingredients"][0]["ingredient_name"] == "FlourCopy1"
    assert [t["name"] for t in response.data["tags"]] == ["TagCopy1"]
    assert response.data["reviews"] == []


def test_recipe_copy_requires_authentication():
    owner = User.objects.create_user(username="chefCopy2", password="pw12345")
    original = Recipe.objects.create(name="Toast", steps=["Toast it"], owner=owner)

    client = APIClient()
    response = client.post(f"/api/recipes/{original.id}/copy/")
    assert response.status_code == 401


def test_recipe_copy_404_for_nonexistent_recipe():
    copier = User.objects.create_user(username="copierCopy3", password="pw12345")
    client = APIClient()
    client.force_authenticate(user=copier)
    response = client.post("/api/recipes/999999/copy/")
    assert response.status_code == 404
    assert response.data["code"] == "not_found"


def test_recipe_copy_survives_deletion_of_original():
    owner = User.objects.create_user(username="chefCopy4", password="pw12345")
    copier = User.objects.create_user(username="copierCopy4", password="pw12345")
    original = Recipe.objects.create(name="Cookies", steps=["Bake"], owner=owner)

    client = APIClient()
    client.force_authenticate(user=copier)
    copy_response = client.post(f"/api/recipes/{original.id}/copy/")
    copy_id = copy_response.data["id"]
    assert copy_response.data["original_owner"] == "chefCopy4"

    original.delete()

    detail_response = client.get(f"/api/recipes/{copy_id}/")
    assert detail_response.status_code == 200
    assert detail_response.data["original_recipe"] is None
    assert detail_response.data["original_owner"] == "chefCopy4"
