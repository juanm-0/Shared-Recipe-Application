from rest_framework import serializers
from accounts.permissions import is_owner_or_staff
from .models import Ingredient, Recipe, RecipeIngredient, Review, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ["id", "name"]

class RecipeListSerializer(serializers.ModelSerializer):
    average_rating = serializers.FloatField(read_only=True, allow_null=True)
    review_count = serializers.IntegerField(read_only=True)
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ["id", "name", "image", "average_rating", "review_count", "tags"]

    def get_tags(self, obj):
        return TagSerializer(
            [recipe_tag.tag for recipe_tag in obj.recipe_tags.all()[:3]], many=True
        ).data


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    ingredient_name = serializers.CharField(source="ingredient.name", read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ["ingredient_name", "amount", "unit", "order"]


class ReviewReadSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "username", "rating", "comment", "created_at", "updated_at"]


class RecipeDetailSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientReadSerializer(source="recipe_ingredients", many=True, read_only=True)
    tags = serializers.SerializerMethodField()
    reviews = ReviewReadSerializer(many=True, read_only=True)
    owner = serializers.CharField(source="owner.username", read_only=True)
    original_recipe = serializers.PrimaryKeyRelatedField(read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            "id", "name", "steps", "image", "owner", "original_recipe",
            "ingredients", "tags", "reviews", "can_edit",
            "created_at", "updated_at",
        ]

    def get_tags(self, obj):
        return TagSerializer(
            [recipe_tag.tag for recipe_tag in obj.recipe_tags.all()], many=True
        ).data

    def get_can_edit(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return is_owner_or_staff(request.user, obj)
