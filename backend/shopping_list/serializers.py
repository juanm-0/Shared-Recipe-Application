from rest_framework import serializers

from recipes.models import Ingredient, RecipeIngredient
from recipes.utils import get_or_create_ci

from .models import ShoppingList, ShoppingListItem
from .services import get_or_create_shopping_list, merge_or_create_item


class ShoppingListItemSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source="ingredient.name", read_only=True)

    class Meta:
        model = ShoppingListItem
        fields = ["id", "ingredient_name", "amount", "unit", "is_checked", "source_recipe"]

class ShoppingListItemUpdateSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        model = ShoppingListItem
        fields = ["amount"]

    def update(self, instance, validated_data):
        instance.amount = validated_data.get("amount", instance.amount)
        instance.full_clean()
        instance.save()
        return instance
    

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
        return merge_or_create_item(
            shopping_list, ingredient, validated_data["amount"], validated_data["unit"]
        )


class ShoppingListImportSerializer(serializers.Serializer):
    recipe_id = serializers.IntegerField()
