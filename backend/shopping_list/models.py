from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from recipes.models import Ingredient, Recipe, RecipeIngredient


class ShoppingList(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shopping_list"
    )

    def __str__(self):
        return f"{self.user}'s shopping list"


class ShoppingListItem(models.Model):
    shopping_list = models.ForeignKey(
        ShoppingList, on_delete=models.CASCADE, related_name="items"
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.PROTECT, related_name="shopping_list_items"
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(max_length=20, choices=RecipeIngredient.UNIT_CHOICES)
    is_checked = models.BooleanField(default=False)
    source_recipe = models.ForeignKey(
        Recipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shopping_list_items",
    )

    class Meta:
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0), name="shoppinglistitem_amount_gt_0"
            ),
        ]

    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "Amount must be greater than zero."})

    def __str__(self):
        return f"{self.amount} {self.unit} {self.ingredient}"
