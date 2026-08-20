from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from recipes.models import Ingredient
from shopping_list.models import ShoppingList, ShoppingListItem

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_user_can_only_have_one_shopping_list():
    user = User.objects.create_user(username="lister1", password="pw12345")
    ShoppingList.objects.create(user=user)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ShoppingList.objects.create(user=user)


def test_deleting_ingredient_in_use_is_protected():
    user = User.objects.create_user(username="lister2", password="pw12345")
    shopping_list = ShoppingList.objects.create(user=user)
    flour = Ingredient.objects.create(name="Flour Protected")
    ShoppingListItem.objects.create(
        shopping_list=shopping_list, ingredient=flour, amount=Decimal("2"), unit="cup"
    )
    with pytest.raises(ProtectedError):
        flour.delete()


def test_deleting_unused_ingredient_succeeds():
    flour = Ingredient.objects.create(name="Unused Flour")
    flour.delete()
    assert not Ingredient.objects.filter(name="Unused Flour").exists()


def test_shopping_list_item_amount_must_be_positive():
    user = User.objects.create_user(username="lister3", password="pw12345")
    shopping_list = ShoppingList.objects.create(user=user)
    flour = Ingredient.objects.create(name="Flour Zero Amount")
    item = ShoppingListItem(
        shopping_list=shopping_list, ingredient=flour, amount=Decimal("0"), unit="cup"
    )
    with pytest.raises(ValidationError):
        item.full_clean()
