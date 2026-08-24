import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
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


def test_staff_without_admin_group_cannot_update_others_review():
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
    assert response.status_code == 403


def test_admin_group_member_can_update_any_review():
    owner = User.objects.create_user(username="chef11", password="pw12345")
    reviewer = User.objects.create_user(username="reviewer11", password="pw12345")
    moderator = User.objects.create_user(username="moderator11", password="pw12345")
    moderator.groups.add(Group.objects.get(name="Admin"))
    recipe = _make_recipe(owner)
    review = Review.objects.create(recipe=recipe, user=reviewer, rating=3, comment="Ok")

    client = APIClient()
    client.force_authenticate(user=moderator)
    response = client.patch(
        f"/api/recipes/{recipe.id}/reviews/{review.id}/", {"rating": 1}, format="json"
    )
    assert response.status_code == 200


def test_review_detail_404_when_review_belongs_to_other_recipe():
    owner1 = User.objects.create_user(username="chefA", password="pw12345")
    owner2 = User.objects.create_user(username="chefB", password="pw12345")
    reviewer = User.objects.create_user(username="reviewerX", password="pw12345")
    recipe_a = _make_recipe(owner1, name="Recipe A")
    recipe_b = _make_recipe(owner2, name="Recipe B")
    review = Review.objects.create(recipe=recipe_a, user=reviewer, rating=3, comment="On A")

    client = APIClient()
    client.force_authenticate(user=reviewer)

    patch_response = client.patch(
        f"/api/recipes/{recipe_b.id}/reviews/{review.id}/", {"rating": 5}, format="json"
    )
    assert patch_response.status_code == 404

    delete_response = client.delete(f"/api/recipes/{recipe_b.id}/reviews/{review.id}/")
    assert delete_response.status_code == 404

    review.refresh_from_db()
    assert review.rating == 3


def test_review_appears_in_recipe_detail_after_create_and_disappears_after_delete():
    owner = User.objects.create_user(username="chefDetail", password="pw12345")
    reviewer = User.objects.create_user(username="reviewerDetail", password="pw12345")
    recipe = _make_recipe(owner)

    client = APIClient()
    client.force_authenticate(user=reviewer)

    create_response = client.post(
        f"/api/recipes/{recipe.id}/reviews/", {"rating": 4, "comment": "Nice"}, format="json"
    )
    review_id = create_response.data["id"]

    detail_response = client.get(f"/api/recipes/{recipe.id}/")
    review_ids = [r["id"] for r in detail_response.data["reviews"]]
    assert review_id in review_ids

    client.delete(f"/api/recipes/{recipe.id}/reviews/{review_id}/")

    detail_response_after = client.get(f"/api/recipes/{recipe.id}/")
    review_ids_after = [r["id"] for r in detail_response_after.data["reviews"]]
    assert review_id not in review_ids_after


def test_review_update_rejects_rating_out_of_range():
    owner = User.objects.create_user(username="chefUpdRange", password="pw12345")
    reviewer = User.objects.create_user(username="reviewerUpdRange", password="pw12345")
    recipe = _make_recipe(owner)
    review = Review.objects.create(recipe=recipe, user=reviewer, rating=3, comment="Ok")

    client = APIClient()
    client.force_authenticate(user=reviewer)
    response = client.patch(
        f"/api/recipes/{recipe.id}/reviews/{review.id}/", {"rating": 7}, format="json"
    )
    assert response.status_code == 400
    review.refresh_from_db()
    assert review.rating == 3


def test_review_update_requires_authentication():
    owner = User.objects.create_user(username="chefAuthUpd", password="pw12345")
    reviewer = User.objects.create_user(username="reviewerAuthUpd", password="pw12345")
    recipe = _make_recipe(owner)
    review = Review.objects.create(recipe=recipe, user=reviewer, rating=3, comment="Ok")

    client = APIClient()
    response = client.patch(
        f"/api/recipes/{recipe.id}/reviews/{review.id}/", {"rating": 5}, format="json"
    )
    assert response.status_code == 401


def test_review_delete_requires_authentication():
    owner = User.objects.create_user(username="chefAuthDel", password="pw12345")
    reviewer = User.objects.create_user(username="reviewerAuthDel", password="pw12345")
    recipe = _make_recipe(owner)
    review = Review.objects.create(recipe=recipe, user=reviewer, rating=3, comment="Ok")

    client = APIClient()
    response = client.delete(f"/api/recipes/{recipe.id}/reviews/{review.id}/")
    assert response.status_code == 401
