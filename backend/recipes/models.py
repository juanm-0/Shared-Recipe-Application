from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower


class Tag(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        constraints = [
            UniqueConstraint(Lower("name"), name="unique_tag_name_ci"),
        ]

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        constraints = [
            UniqueConstraint(Lower("name"), name="unique_ingredient_name_ci"),
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(max_length=200)
    steps = models.JSONField(default=list)
    image = models.ImageField(upload_to="recipes/", blank=True, null=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recipes"
    )
    original_recipe = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="copies",
    )
    original_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    UNIT_CHOICES = [
        ("g", "Gram"),
        ("kg", "Kilogram"),
        ("ml", "Milliliter"),
        ("l", "Liter"),
        ("cup", "Cup"),
        ("tbsp", "Tablespoon"),
        ("tsp", "Teaspoon"),
        ("pinch", "Pinch"),
        ("dash", "Dash"),
        ("to_taste", "To taste"),
        ("whole", "Whole"),
        ("clove", "Clove"),
    ]

    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="recipe_ingredients"
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.PROTECT, related_name="recipe_ingredients"
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    order = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gt=0), name="recipeingredient_amount_gt_0"
            ),
        ]
        unique_together = [
            ("recipe", "order"),
            ("recipe", "ingredient"),
        ]
        ordering = ["order"]

    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "Amount must be greater than zero."})

    def __str__(self):
        return f"{self.amount} {self.unit} {self.ingredient}"
