import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from recipes.models import Ingredient, Tag, Recipe

pytestmark = pytest.mark.django_db

User = get_user_model()


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


def test_copy_lineage_survives_deletion_of_original_recipe():
    original_owner = User.objects.create_user(username="alice", password="pw12345")
    copier = User.objects.create_user(username="bob", password="pw12345")
    original = Recipe.objects.create(
        name="Chili", steps=["Brown the beef", "Simmer"], owner=original_owner
    )

    copy = Recipe.objects.create(
        name="Chili",
        steps=["Brown the beef", "Simmer"],
        owner=copier,
        original_recipe=original,
        original_owner=original_owner,
    )

    original.delete()
    copy.refresh_from_db()

    assert copy.original_recipe is None
    assert copy.original_owner == original_owner


def test_original_owner_cleared_when_original_owner_account_deleted():
    original_owner = User.objects.create_user(username="carol", password="pw12345")
    copier = User.objects.create_user(username="dave", password="pw12345")
    original = Recipe.objects.create(name="Soup", steps=["Boil"], owner=original_owner)
    copy = Recipe.objects.create(
        name="Soup",
        steps=["Boil"],
        owner=copier,
        original_recipe=original,
        original_owner=original_owner,
    )

    original_owner.delete()
    copy.refresh_from_db()

    assert copy.original_owner is None
