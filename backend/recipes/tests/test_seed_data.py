import pytest
from decimal import Decimal
from django.contrib.auth import authenticate, get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from recipes.models import Ingredient, Recipe, RecipeIngredient, RecipeTag, Review, Tag
from shopping_list.models import ShoppingList, ShoppingListItem

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_seed_creates_requested_number_of_users():
    call_command("seed_data", "--users=5", "--recipes=0")
    assert User.objects.filter(is_staff=False, is_superuser=False).count() == 5


def test_seed_users_have_known_password():
    call_command("seed_data", "--users=1", "--recipes=0")
    user = User.objects.filter(is_staff=False, is_superuser=False).first()
    assert authenticate(username=user.username, password="seedpass123") is not None


def test_seed_catalog_is_idempotent_across_two_runs():
    call_command("seed_data", "--users=0", "--recipes=0")
    first_ingredient_count = Ingredient.objects.count()
    first_tag_count = Tag.objects.count()
    call_command("seed_data", "--users=0", "--recipes=0")
    assert Ingredient.objects.count() == first_ingredient_count
    assert Tag.objects.count() == first_tag_count
    assert first_ingredient_count > 0
    assert first_tag_count > 0


def test_clear_removes_non_staff_users_but_preserves_staff():
    staff_user = User.objects.create_user(username="admin_seed_test", password="pw12345", is_staff=True)
    call_command("seed_data", "--users=3", "--recipes=0")
    assert User.objects.filter(is_staff=False, is_superuser=False).count() == 3

    call_command("seed_data", "--users=0", "--recipes=0", "--clear")

    assert User.objects.filter(is_staff=False, is_superuser=False).count() == 0
    assert User.objects.filter(pk=staff_user.pk).exists()


def test_clear_preserves_superuser_that_is_not_staff():
    superuser = User.objects.create_user(username="super_seed_test", password="pw12345", is_superuser=True)
    call_command("seed_data", "--users=3", "--recipes=0")

    call_command("seed_data", "--users=0", "--recipes=0", "--clear")

    assert User.objects.filter(pk=superuser.pk).exists()


def test_clear_recreates_catalog_with_fresh_rows():
    call_command("seed_data", "--users=0", "--recipes=0")
    old_ids = set(Ingredient.objects.values_list("pk", flat=True))
    assert old_ids

    call_command("seed_data", "--users=0", "--recipes=0", "--clear")

    new_ids = set(Ingredient.objects.values_list("pk", flat=True))
    assert new_ids
    assert old_ids.isdisjoint(new_ids)


def test_clear_then_reseed_with_recipes_works_end_to_end():
    call_command("seed_data", "--users=5", "--recipes=10")

    call_command("seed_data", "--users=5", "--recipes=10", "--clear")

    assert User.objects.filter(is_staff=False, is_superuser=False).count() == 5
    assert Recipe.objects.count() == 10
    assert Ingredient.objects.exists()
    assert Tag.objects.exists()


def test_clear_does_not_crash_when_staff_user_owns_referenced_catalog_data():
    staff_user = User.objects.create_user(username="admin_owns_data", password="pw12345", is_staff=True)
    call_command("seed_data", "--users=0", "--recipes=0")
    flour = Ingredient.objects.get(name="Flour")
    recipe = Recipe.objects.create(name="Staff Recipe", steps=["Mix"], owner=staff_user)
    RecipeIngredient.objects.create(recipe=recipe, ingredient=flour, amount=Decimal("1"), unit="cup", order=0)

    call_command("seed_data", "--users=0", "--recipes=0", "--clear")

    assert Recipe.objects.filter(pk=recipe.pk).exists()
    assert Ingredient.objects.filter(pk=flour.pk).exists()


def test_running_twice_without_clear_does_not_collide_on_username():
    call_command("seed_data", "--users=5", "--recipes=0")
    call_command("seed_data", "--users=5", "--recipes=0")
    assert User.objects.filter(is_staff=False, is_superuser=False).count() == 10


def test_negative_users_is_rejected():
    with pytest.raises(CommandError):
        call_command("seed_data", "--users=-1", "--recipes=0")


def test_negative_recipes_is_rejected():
    with pytest.raises(CommandError):
        call_command("seed_data", "--users=0", "--recipes=-1")


def test_seed_creates_requested_number_of_recipes():
    call_command("seed_data", "--users=5", "--recipes=10")
    assert Recipe.objects.count() == 10


def test_recipes_with_zero_new_users_falls_back_to_existing_users():
    call_command("seed_data", "--users=5", "--recipes=0")
    call_command("seed_data", "--users=0", "--recipes=10")
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


def test_seeded_recipe_ingredients_have_positive_decimal_amounts():
    call_command("seed_data", "--users=3", "--recipes=20")
    assert RecipeIngredient.objects.exists()
    for ri in RecipeIngredient.objects.all():
        assert isinstance(ri.amount, Decimal)
        assert ri.amount > 0


def test_seeded_recipe_ingredients_respect_unique_together():
    call_command("seed_data", "--users=3", "--recipes=20")
    for recipe in Recipe.objects.all():
        ingredient_ids = list(recipe.recipe_ingredients.values_list("ingredient_id", flat=True))
        orders = list(recipe.recipe_ingredients.values_list("order", flat=True))
        assert len(ingredient_ids) == len(set(ingredient_ids))
        assert len(orders) == len(set(orders))


def test_seeded_reviews_never_include_the_recipes_own_owner():
    call_command("seed_data", "--users=5", "--recipes=20")
    assert Review.objects.exists()
    for review in Review.objects.select_related("recipe"):
        assert review.user_id != review.recipe.owner_id


def test_seeded_reviews_respect_unique_together():
    call_command("seed_data", "--users=5", "--recipes=20")
    assert Review.objects.exists()
    for recipe in Recipe.objects.all():
        reviewer_ids = list(recipe.reviews.values_list("user_id", flat=True))
        assert len(reviewer_ids) == len(set(reviewer_ids))


def test_zero_recipes_produces_no_recipes():
    call_command("seed_data", "--users=5", "--recipes=0")
    assert Recipe.objects.count() == 0


def test_some_users_get_shopping_list_items():
    call_command("seed_data", "--users=10", "--recipes=10")
    lists_with_items = ShoppingList.objects.filter(items__isnull=False).distinct().count()
    assert lists_with_items > 0


def test_shopping_list_items_from_import_have_source_recipe_set():
    call_command("seed_data", "--users=10", "--recipes=10")
    assert ShoppingListItem.objects.filter(source_recipe__isnull=False).exists()


def test_seed_data_with_zero_recipes_does_not_crash_shopping_list_seeding():
    call_command("seed_data", "--users=5", "--recipes=0")
    assert ShoppingList.objects.count() == 0


def test_seed_data_rolls_back_fully_on_forced_failure(monkeypatch):
    from recipes.management.commands.seed_data import Command

    def _broken_seed_shopping_lists(self, users, recipes):
        raise RuntimeError("forced failure for rollback test")

    monkeypatch.setattr(Command, "_seed_shopping_lists", _broken_seed_shopping_lists)

    with pytest.raises(RuntimeError):
        call_command("seed_data", "--users=3", "--recipes=3")

    assert User.objects.filter(is_staff=False, is_superuser=False).count() == 0
    assert Recipe.objects.count() == 0
