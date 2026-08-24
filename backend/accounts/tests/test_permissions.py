from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from accounts.permissions import IsOwnerOrHasPermission
from recipes.models import Recipe, Review

pytestmark = pytest.mark.django_db

User = get_user_model()


def _request_for(user, method="PATCH"):
    return SimpleNamespace(user=user, method=method)


def test_owner_can_access_recipe():
    owner = User.objects.create_user(username="owner1", password="pw12345")
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)
    assert IsOwnerOrHasPermission().has_object_permission(_request_for(owner), None, recipe) is True


def test_non_owner_cannot_access_recipe():
    owner = User.objects.create_user(username="owner2", password="pw12345")
    other = User.objects.create_user(username="other2", password="pw12345")
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)
    assert IsOwnerOrHasPermission().has_object_permission(_request_for(other), None, recipe) is False


def test_staff_without_admin_group_cannot_access_others_recipe():
    owner = User.objects.create_user(username="owner3", password="pw12345")
    staff = User.objects.create_user(username="staff3", password="pw12345", is_staff=True)
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)
    assert IsOwnerOrHasPermission().has_object_permission(_request_for(staff), None, recipe) is False


def test_admin_group_member_can_edit_and_delete_any_recipe():
    owner = User.objects.create_user(username="owner6", password="pw12345")
    admin_group = Group.objects.get(name="Admin")
    moderator = User.objects.create_user(username="moderator6", password="pw12345")
    moderator.groups.add(admin_group)
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)
    assert IsOwnerOrHasPermission().has_object_permission(_request_for(moderator, method="PATCH"), None, recipe) is True
    assert IsOwnerOrHasPermission().has_object_permission(_request_for(moderator, method="DELETE"), None, recipe) is True


def test_user_group_member_cannot_access_others_recipe():
    owner = User.objects.create_user(username="owner7", password="pw12345")
    user_group = Group.objects.get(name="User")
    member = User.objects.create_user(username="member7", password="pw12345")
    member.groups.add(user_group)
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)
    assert IsOwnerOrHasPermission().has_object_permission(_request_for(member), None, recipe) is False


def test_review_author_can_access_own_review():
    owner = User.objects.create_user(username="owner4", password="pw12345")
    reviewer = User.objects.create_user(username="reviewer4", password="pw12345")
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)
    review = Review.objects.create(recipe=recipe, user=reviewer, rating=5, comment="Great")
    assert IsOwnerOrHasPermission().has_object_permission(_request_for(reviewer), None, review) is True


def test_non_author_cannot_access_others_review():
    owner = User.objects.create_user(username="owner5", password="pw12345")
    reviewer = User.objects.create_user(username="reviewer5", password="pw12345")
    other = User.objects.create_user(username="other5", password="pw12345")
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)
    review = Review.objects.create(recipe=recipe, user=reviewer, rating=5, comment="Great")
    assert IsOwnerOrHasPermission().has_object_permission(_request_for(other), None, review) is False


def test_admin_group_member_can_access_others_review():
    owner = User.objects.create_user(username="owner8", password="pw12345")
    reviewer = User.objects.create_user(username="reviewer8", password="pw12345")
    admin_group = Group.objects.get(name="Admin")
    moderator = User.objects.create_user(username="moderator8", password="pw12345")
    moderator.groups.add(admin_group)
    recipe = Recipe.objects.create(name="Soup", steps=["Boil"], owner=owner)
    review = Review.objects.create(recipe=recipe, user=reviewer, rating=5, comment="Great")
    assert IsOwnerOrHasPermission().has_object_permission(_request_for(moderator, method="DELETE"), None, review) is True
