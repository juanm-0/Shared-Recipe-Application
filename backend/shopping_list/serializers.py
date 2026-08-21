from rest_framework import serializers

from recipes.models import Ingredient, RecipeIngredient
from recipes.utils import get_or_create_ci

from .models import ShoppingList, ShoppingListItem
from .services import get_or_create_shopping_list


class ShoppingListItemSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source="ingredient.name", read_only=True)

    class Meta:
        model = ShoppingListItem
        fields = ["id", "ingredient_name", "amount", "unit", "is_checked", "source_recipe"]


class ShoppingListSerializer(serializers.ModelSerializer):
    items = ShoppingListItemSerializer(many=True, read_only=True)

    class Meta:
        model = ShoppingList
        fields = ["id", "items"]


class ShoppingListItemCreateSerializer(serializers.Serializer):
    ingredient_name = serializers.CharField(max_length=200)
    amount = serializers.DecimalField(max_digits=8, decimal_places=2)
    unit = serializers.ChoiceField(choices=RecipeIngredient.UNIT_CHOICES)

    def create(self, validated_data):
        user = self.context["request"].user
        shopping_list = get_or_create_shopping_list(user)
        ingredient = get_or_create_ci(Ingredient, validated_data["ingredient_name"])
        item = ShoppingListItem(
            shopping_list=shopping_list,
            ingredient=ingredient,
            amount=validated_data["amount"],
            unit=validated_data["unit"],
        )
        item.full_clean()
        item.save()
        return item


class ShoppingListImportSerializer(serializers.Serializer):
    recipe_id = serializers.IntegerField()
