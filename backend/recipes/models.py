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
