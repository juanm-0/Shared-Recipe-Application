from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model

from accounts.permissions import IsOwnerOrStaff
from recipes.models import Recipe, Review

pytestmark = pytest.mark.django_db

User = get_user_model()


def _request_for(user):
    return SimpleNamespace(user=user)


def test_owner_can_access_recipe():
    owner = User.objects.create_user(username="owner1", password="pw12345")
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)
    assert IsOwnerOrStaff().has_object_permission(_request_for(owner), None, recipe) is True


def test_non_owner_cannot_access_recipe():
    owner = User.objects.create_user(username="owner2", password="pw12345")
    other = User.objects.create_user(username="other2", password="pw12345")
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)
    assert IsOwnerOrStaff().has_object_permission(_request_for(other), None, recipe) is False


def test_staff_can_access_any_recipe():
    owner = User.objects.create_user(username="owner3", password="pw12345")
    staff = User.objects.create_user(username="staff3", password="pw12345", is_staff=True)
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)
    assert IsOwnerOrStaff().has_object_permission(_request_for(staff), None, recipe) is True


def test_review_author_can_access_own_review():
    owner = User.objects.create_user(username="owner4", password="pw12345")
    reviewer = User.objects.create_user(username="reviewer4", password="pw12345")
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)
    review = Review.objects.create(recipe=recipe, user=reviewer, rating=5, comment="Great")
    assert IsOwnerOrStaff().has_object_permission(_request_for(reviewer), None, review) is True


def test_non_author_cannot_access_others_review():
    owner = User.objects.create_user(username="owner5", password="pw12345")
    reviewer = User.objects.create_user(username="reviewer5", password="pw12345")
    other = User.objects.create_user(username="other5", password="pw12345")
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)
    review = Review.objects.create(recipe=recipe, user=reviewer, rating=5, comment="Great")
    assert IsOwnerOrStaff().has_object_permission(_request_for(other), None, review) is False
