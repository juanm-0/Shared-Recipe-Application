import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from recipes.models import Ingredient, Tag, Recipe, Review

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


from decimal import Decimal

from django.core.exceptions import ValidationError

from recipes.models import RecipeIngredient


def _make_recipe(username="chef"):
    owner = User.objects.create_user(username=username, password="pw12345")
    return Recipe.objects.create(name="Pancakes", steps=["Mix", "Cook"], owner=owner)


def test_recipe_ingredient_amount_must_be_positive():
    recipe = _make_recipe("chef-amount")
    flour = Ingredient.objects.create(name="Flour A")
    line = RecipeIngredient(
        recipe=recipe, ingredient=flour, amount=Decimal("0"), unit="cup", order=1
    )
    with pytest.raises(ValidationError):
        line.full_clean()


def test_recipe_ingredient_accepts_positive_amount():
    recipe = _make_recipe("chef-positive")
    flour = Ingredient.objects.create(name="Flour B")
    line = RecipeIngredient(
        recipe=recipe, ingredient=flour, amount=Decimal("1.5"), unit="cup", order=1
    )
    line.full_clean()
    line.save()
    assert RecipeIngredient.objects.count() == 1


def test_recipe_ingredient_order_is_unique_per_recipe():
    recipe = _make_recipe("chef-order")
    flour = Ingredient.objects.create(name="Flour C")
    sugar = Ingredient.objects.create(name="Sugar C")
    RecipeIngredient.objects.create(
        recipe=recipe, ingredient=flour, amount=Decimal("1"), unit="cup", order=1
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient=sugar, amount=Decimal("1"), unit="cup", order=1
            )


def test_recipe_ingredient_cannot_reference_same_ingredient_twice():
    recipe = _make_recipe("chef-dup")
    flour = Ingredient.objects.create(name="Flour D")
    RecipeIngredient.objects.create(
        recipe=recipe, ingredient=flour, amount=Decimal("1"), unit="cup", order=1
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient=flour, amount=Decimal("2"), unit="tbsp", order=2
            )


from recipes.models import RecipeTag


def test_recipe_rejects_sixth_tag():
    recipe = _make_recipe("chef-sixth-tag")
    for i in range(5):
        tag = Tag.objects.create(name=f"tag-{i}")
        RecipeTag.objects.create(recipe=recipe, tag=tag, order=i)

    sixth_tag = Tag.objects.create(name="tag-5")
    sixth = RecipeTag(recipe=recipe, tag=sixth_tag, order=5)
    with pytest.raises(ValidationError):
        sixth.full_clean()


def test_recipe_accepts_up_to_five_tags():
    recipe = _make_recipe("chef-five-tags")
    for i in range(5):
        tag = Tag.objects.create(name=f"tag-ok-{i}")
        rt = RecipeTag(recipe=recipe, tag=tag, order=i)
        rt.full_clean()
        rt.save()
    assert RecipeTag.objects.filter(recipe=recipe).count() == 5


def test_recipe_tag_order_is_unique_per_recipe():
    recipe = _make_recipe("chef-tag-order")
    tag_a = Tag.objects.create(name="tag-a")
    tag_b = Tag.objects.create(name="tag-b")
    RecipeTag.objects.create(recipe=recipe, tag=tag_a, order=1)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            RecipeTag.objects.create(recipe=recipe, tag=tag_b, order=1)


def test_recipe_cannot_have_same_tag_twice():
    recipe = _make_recipe("chef-tag-dup")
    tag = Tag.objects.create(name="tag-dup")
    RecipeTag.objects.create(recipe=recipe, tag=tag, order=1)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            RecipeTag.objects.create(recipe=recipe, tag=tag, order=2)


def test_user_cannot_review_same_recipe_twice():
    recipe = _make_recipe("chef-review-1")
    reviewer = User.objects.create_user(username="reviewer1", password="pw12345")
    Review.objects.create(recipe=recipe, user=reviewer, rating=4, comment="Good")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Review.objects.create(recipe=recipe, user=reviewer, rating=5, comment="Great")


def test_different_users_can_each_review_same_recipe():
    recipe = _make_recipe("chef-review-2")
    reviewer_a = User.objects.create_user(username="reviewer2", password="pw12345")
    reviewer_b = User.objects.create_user(username="reviewer3", password="pw12345")
    Review.objects.create(recipe=recipe, user=reviewer_a, rating=3, comment="Ok")
    Review.objects.create(recipe=recipe, user=reviewer_b, rating=5, comment="Loved it")
    assert Review.objects.filter(recipe=recipe).count() == 2


def test_review_rating_must_be_between_one_and_five():
    recipe = _make_recipe("chef-review-3")
    reviewer = User.objects.create_user(username="reviewer4", password="pw12345")
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Review.objects.create(recipe=recipe, user=reviewer, rating=6, comment="Too high")
