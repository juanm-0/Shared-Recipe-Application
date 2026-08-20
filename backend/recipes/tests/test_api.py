import pytest
from rest_framework.test import APIClient

from recipes.models import Ingredient, Tag

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
