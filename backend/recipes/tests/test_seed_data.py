import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.management import call_command

from recipes.models import Ingredient, Recipe, RecipeTag, Review, Tag

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_seed_creates_requested_number_of_users():
    call_command("seed_data", "--users=5", "--recipes=0")
    assert User.objects.filter(is_staff=False, is_superuser=False).count() == 5


def test_seed_users_have_known_password():
    call_command("seed_data", "--users=1", "--recipes=0")
    user = User.objects.filter(is_staff=False, is_superuser=False).first()
    assert check_password("seedpass123", user.password)


def test_seed_catalog_is_idempotent_across_two_runs():
    call_command("seed_data", "--users=0", "--recipes=0")
    first_count = Ingredient.objects.count()
    call_command("seed_data", "--users=0", "--recipes=0")
    second_count = Ingredient.objects.count()
    assert first_count == second_count
    assert first_count > 0


def test_clear_removes_non_staff_users_but_preserves_staff():
    staff_user = User.objects.create_user(username="admin_seed_test", password="pw12345", is_staff=True)
    call_command("seed_data", "--users=3", "--recipes=0")
    assert User.objects.filter(is_staff=False, is_superuser=False).count() == 3

    call_command("seed_data", "--users=0", "--recipes=0", "--clear")

    assert User.objects.filter(is_staff=False, is_superuser=False).count() == 0
    assert User.objects.filter(pk=staff_user.pk).exists()


def test_clear_recreates_catalog_with_fresh_rows():
    call_command("seed_data", "--users=0", "--recipes=0")
    old_ids = set(Ingredient.objects.values_list("pk", flat=True))
    assert old_ids

    call_command("seed_data", "--users=0", "--recipes=0", "--clear")

    new_ids = set(Ingredient.objects.values_list("pk", flat=True))
    assert new_ids
    assert old_ids.isdisjoint(new_ids)


def test_running_twice_without_clear_does_not_collide_on_username():
    call_command("seed_data", "--users=5", "--recipes=0")
    call_command("seed_data", "--users=5", "--recipes=0")
    assert User.objects.filter(is_staff=False, is_superuser=False).count() == 10


def test_seed_creates_requested_number_of_recipes():
    call_command("seed_data", "--users=5", "--recipes=10")
    assert Recipe.objects.count() == 10


def test_seeded_recipes_have_at_least_one_ingredient_and_step():
    call_command("seed_data", "--users=3", "--recipes=5")
    for recipe in Recipe.objects.all():
        assert recipe.recipe_ingredients.exists()
        assert len(recipe.steps) >= 1


def test_seeded_recipes_respect_max_tags():
    call_command("seed_data", "--users=3", "--recipes=20")
    for recipe in Recipe.objects.all():
        assert recipe.recipe_tags.count() <= RecipeTag.MAX_TAGS


def test_seeded_reviews_never_include_the_recipes_own_owner():
    call_command("seed_data", "--users=5", "--recipes=20")
    for review in Review.objects.select_related("recipe"):
        assert review.user_id != review.recipe.owner_id


def test_seeded_reviews_respect_unique_together():
    call_command("seed_data", "--users=5", "--recipes=20")
    for recipe in Recipe.objects.all():
        reviewer_ids = list(recipe.reviews.values_list("user_id", flat=True))
        assert len(reviewer_ids) == len(set(reviewer_ids))


def test_zero_recipes_produces_no_recipes():
    call_command("seed_data", "--users=5", "--recipes=0")
    assert Recipe.objects.count() == 0
