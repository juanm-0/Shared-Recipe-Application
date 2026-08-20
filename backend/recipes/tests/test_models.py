import pytest
from django.db import IntegrityError, transaction

from recipes.models import Ingredient, Tag

pytestmark = pytest.mark.django_db


def test_tag_name_is_case_insensitively_unique():
    Tag.objects.create(name="Vegan")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Tag.objects.create(name="vegan")


def test_tag_allows_distinct_names():
    Tag.objects.create(name="Vegan")
    Tag.objects.create(name="Gluten-Free")
    assert Tag.objects.count() == 2


def test_ingredient_name_is_case_insensitively_unique():
    Ingredient.objects.create(name="Flour")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Ingredient.objects.create(name="FLOUR")


def test_ingredient_allows_distinct_names():
    Ingredient.objects.create(name="Flour")
    Ingredient.objects.create(name="Sugar")
    assert Ingredient.objects.count() == 2
