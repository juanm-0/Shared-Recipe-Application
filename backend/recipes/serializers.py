from concurrency.exceptions import RecordModifiedError
from django.db import IntegrityError, transaction
from rest_framework import serializers
from accounts.permissions import is_owner_or_staff
from .exceptions import DuplicateReview, StaleWrite, TagLimitExceeded
from .models import Ingredient, Recipe, RecipeIngredient, RecipeTag, Review, Tag
from .utils import get_or_create_ci


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
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ["id", "name", "image", "average_rating", "review_count", "tags"]

    def get_tags(self, obj):
        return TagSerializer(
            [recipe_tag.tag for recipe_tag in obj.recipe_tags.all()[:3]], many=True
        ).data

    def get_image(self, obj):
        return obj.image.url if obj.image else None


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
    original_owner = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    version = serializers.IntegerField(read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            "id", "name", "steps", "image", "owner", "original_recipe", "original_owner",
            "ingredients", "tags", "reviews", "can_edit", "version",
            "created_at", "updated_at",
        ]

    def get_tags(self, obj):
        return TagSerializer(
            [recipe_tag.tag for recipe_tag in obj.recipe_tags.all()], many=True
        ).data

    def get_image(self, obj):
        return obj.image.url if obj.image else None

    def get_can_edit(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return is_owner_or_staff(request.user, obj)

    def get_original_owner(self, obj):
        if obj.original_owner is None:
            return None
        return obj.original_owner.username


class RecipeIngredientWriteSerializer(serializers.Serializer):
    ingredient_name = serializers.CharField(max_length=200)
    amount = serializers.DecimalField(max_digits=8, decimal_places=2)
    unit = serializers.ChoiceField(choices=RecipeIngredient.UNIT_CHOICES)


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientWriteSerializer(many=True)
    tags = serializers.ListField(child=serializers.CharField(max_length=100), required=False, default=list)
    version = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Recipe
        fields = ["name", "steps", "image", "ingredients", "tags", "version"]

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("A recipe must have at least one ingredient.")
        return value

    def validate_steps(self, value):
        if not value:
            raise serializers.ValidationError("A recipe must have at least one step.")
        return value

    def validate_tags(self, value):
        if len(value) > RecipeTag.MAX_TAGS:
            raise TagLimitExceeded(count=len(value))
        return value

    def validate(self, attrs):
        if self.instance is not None:
            version = attrs.get("version")
            if version is None:
                raise serializers.ValidationError(
                    {"version": "This field is required for updates."}
                )
            if version != self.instance.version:
                raise StaleWrite(
                    current_data=RecipeDetailSerializer(self.instance, context=self.context).data
                )
        return attrs

    def create(self, validated_data):
        validated_data.pop("version", None)
        ingredients_data = validated_data.pop("ingredients")
        tags_data = validated_data.pop("tags", [])
        request = self.context["request"]

        with transaction.atomic():
            recipe = Recipe.objects.create(owner=request.user, **validated_data)
            self._set_ingredients(recipe, ingredients_data)
            self._set_tags(recipe, tags_data)
        return recipe

    def update(self, instance, validated_data):
        client_version = validated_data.pop("version", None)
        ingredients_data = validated_data.pop("ingredients", None)
        tags_data = validated_data.pop("tags", None)

        instance.version = client_version
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        try:
            with transaction.atomic():
                instance.save()
                if ingredients_data is not None:
                    self._set_ingredients(instance, ingredients_data)
                if tags_data is not None:
                    self._set_tags(instance, tags_data)
        except RecordModifiedError:
            current = Recipe.objects.get(pk=instance.pk)
            raise StaleWrite(
                current_data=RecipeDetailSerializer(current, context=self.context).data
            )

        instance.refresh_from_db()
        return instance

    def _set_ingredients(self, recipe, ingredients_data):
        recipe.recipe_ingredients.all().delete()
        for order, item in enumerate(ingredients_data):
            ingredient = get_or_create_ci(Ingredient, item["ingredient_name"])
            ri = RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient,
                amount=item["amount"],
                unit=item["unit"],
                order=order,
            )
            ri.full_clean()
            ri.save()

    def _set_tags(self, recipe, tags_data):
        recipe.recipe_tags.all().delete()
        for order, name in enumerate(tags_data):
            tag = get_or_create_ci(Tag, name)
            rt = RecipeTag(recipe=recipe, tag=tag, order=order)
            rt.full_clean()
            rt.save()


class ReviewWriteSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(allow_blank=True, required=False, default="")

    def validate(self, attrs):
        if self.instance is None:
            recipe = self.context["recipe"]
            user = self.context["request"].user
            existing = Review.objects.filter(recipe=recipe, user=user).first()
            if existing is not None:
                raise DuplicateReview(review_id=existing.id)
        return attrs

    def create(self, validated_data):
        recipe = self.context["recipe"]
        user = self.context["request"].user
        review = Review(recipe=recipe, user=user, **validated_data)
        review.full_clean(validate_unique=False)
        try:
            with transaction.atomic():
                review.save()
        except IntegrityError:
            existing = Review.objects.get(recipe=recipe, user=user)
            raise DuplicateReview(review_id=existing.id)
        return review

    def update(self, instance, validated_data):
        instance.rating = validated_data.get("rating", instance.rating)
        instance.comment = validated_data.get("comment", instance.comment)
        instance.full_clean(validate_unique=False)
        instance.save()
        return instance
