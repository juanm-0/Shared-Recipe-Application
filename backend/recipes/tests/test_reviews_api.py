import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from recipes.models import Recipe, Review

pytestmark = pytest.mark.django_db

User = get_user_model()


def _make_recipe(owner, name="Soup"):
    return Recipe.objects.create(name=name, steps=["Boil"], owner=owner)


def test_review_create_happy_path():
    owner = User.objects.create_user(username="chef1", password="pw12345")
    reviewer = User.objects.create_user(username="reviewer1", password="pw12345")
    recipe = _make_recipe(owner)

    client = APIClient()
    client.force_authenticate(user=reviewer)
    response = client.post(
        f"/api/recipes/{recipe.id}/reviews/", {"rating": 5, "comment": "Great!"}, format="json"
    )
    assert response.status_code == 201
    assert response.data["rating"] == 5
    assert response.data["username"] == "reviewer1"
    assert Review.objects.filter(recipe=recipe, user=reviewer).exists()


def test_review_create_rejects_duplicate():
    owner = User.objects.create_user(username="chef2", password="pw12345")
    reviewer = User.objects.create_user(username="reviewer2", password="pw12345")
    recipe = _make_recipe(owner)
    existing = Review.objects.create(recipe=recipe, user=reviewer, rating=4, comment="Good")

    client = APIClient()
    client.force_authenticate(user=reviewer)
    response = client.post(
        f"/api/recipes/{recipe.id}/reviews/", {"rating": 5, "comment": "Again"}, format="json"
    )
    assert response.status_code == 409
    assert response.data["code"] == "duplicate_review"
    assert response.data["review_id"] == existing.id


def test_review_create_rejects_rating_out_of_range():
    owner = User.objects.create_user(username="chef3", password="pw12345")
    reviewer = User.objects.create_user(username="reviewer3", password="pw12345")
    recipe = _make_recipe(owner)

    client = APIClient()
    client.force_authenticate(user=reviewer)
    response = client.post(
        f"/api/recipes/{recipe.id}/reviews/", {"rating": 6, "comment": "Too high"}, format="json"
    )
    assert response.status_code == 400
    assert response.data["code"] == "validation_error"


def test_review_create_404_for_nonexistent_recipe():
    reviewer = User.objects.create_user(username="reviewer4", password="pw12345")
    client = APIClient()
    client.force_authenticate(user=reviewer)
    response = client.post("/api/recipes/999999/reviews/", {"rating": 5, "comment": "x"}, format="json")
    assert response.status_code == 404
    assert response.data["code"] == "not_found"


def test_review_create_requires_authentication():
    owner = User.objects.create_user(username="chef5", password="pw12345")
    recipe = _make_recipe(owner)
    client = APIClient()
    response = client.post(
        f"/api/recipes/{recipe.id}/reviews/", {"rating": 5, "comment": "x"}, format="json"
    )
    assert response.status_code == 401


def test_review_update_happy_path():
    owner = User.objects.create_user(username="chef6", password="pw12345")
    reviewer = User.objects.create_user(username="reviewer6", password="pw12345")
    recipe = _make_recipe(owner)
    review = Review.objects.create(recipe=recipe, user=reviewer, rating=3, comment="Ok")

    client = APIClient()
    client.force_authenticate(user=reviewer)
    response = client.patch(
        f"/api/recipes/{recipe.id}/reviews/{review.id}/", {"rating": 5}, format="json"
    )
    assert response.status_code == 200
    assert response.data["rating"] == 5
    assert response.data["comment"] == "Ok"


def test_review_update_rejects_non_author():
    owner = User.objects.create_user(username="chef7", password="pw12345")
    reviewer = User.objects.create_user(username="reviewer7", password="pw12345")
    other = User.objects.create_user(username="other7", password="pw12345")
    recipe = _make_recipe(owner)
    review = Review.objects.create(recipe=recipe, user=reviewer, rating=3, comment="Ok")

    client = APIClient()
    client.force_authenticate(user=other)
    response = client.patch(
        f"/api/recipes/{recipe.id}/reviews/{review.id}/", {"rating": 1}, format="json"
    )
    assert response.status_code == 403
    review.refresh_from_db()
    assert review.rating == 3


def test_review_delete_happy_path():
    owner = User.objects.create_user(username="chef8", password="pw12345")
    reviewer = User.objects.create_user(username="reviewer8", password="pw12345")
    recipe = _make_recipe(owner)
    review = Review.objects.create(recipe=recipe, user=reviewer, rating=3, comment="Ok")

    client = APIClient()
    client.force_authenticate(user=reviewer)
    response = client.delete(f"/api/recipes/{recipe.id}/reviews/{review.id}/")
    assert response.status_code == 204
    assert not Review.objects.filter(id=review.id).exists()


def test_review_delete_rejects_non_author():
    owner = User.objects.create_user(username="chef9", password="pw12345")
    reviewer = User.objects.create_user(username="reviewer9", password="pw12345")
    other = User.objects.create_user(username="other9", password="pw12345")
    recipe = _make_recipe(owner)
    review = Review.objects.create(recipe=recipe, user=reviewer, rating=3, comment="Ok")

    client = APIClient()
    client.force_authenticate(user=other)
    response = client.delete(f"/api/recipes/{recipe.id}/reviews/{review.id}/")
    assert response.status_code == 403
    assert Review.objects.filter(id=review.id).exists()


def test_staff_can_update_any_review():
    owner = User.objects.create_user(username="chef10", password="pw12345")
    reviewer = User.objects.create_user(username="reviewer10", password="pw12345")
    staff = User.objects.create_user(username="staff10", password="pw12345", is_staff=True)
    recipe = _make_recipe(owner)
    review = Review.objects.create(recipe=recipe, user=reviewer, rating=3, comment="Ok")

    client = APIClient()
    client.force_authenticate(user=staff)
    response = client.patch(
        f"/api/recipes/{recipe.id}/reviews/{review.id}/", {"rating": 1}, format="json"
    )
    assert response.status_code == 200
