import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from recipes.models import Ingredient, Recipe, RecipeIngredient, RecipeTag, Review, Tag
from recipes.utils import get_or_create_ci

User = get_user_model()

SEED_PASSWORD = "seedpass123"

INGREDIENT_POOL = [
    "Flour", "Sugar", "Salt", "Black Pepper", "Olive Oil", "Butter", "Eggs",
    "Milk", "Garlic", "Onion", "Tomato", "Chicken Breast", "Ground Beef",
    "Rice", "Pasta", "Basil", "Oregano", "Cumin", "Paprika", "Cinnamon",
    "Vanilla Extract", "Baking Powder", "Baking Soda", "Honey", "Lemon",
    "Lime", "Ginger", "Soy Sauce", "Vinegar", "Parmesan Cheese",
    "Mozzarella Cheese", "Cheddar Cheese", "Carrots", "Celery", "Potatoes",
    "Sweet Potatoes", "Spinach", "Kale", "Broccoli", "Bell Pepper",
    "Mushrooms", "Zucchini", "Cucumber", "Avocado", "Lettuce", "Cilantro",
    "Parsley", "Thyme", "Rosemary", "Chili Powder", "Red Pepper Flakes",
    "Coconut Milk", "Almond Milk", "Yogurt", "Sour Cream", "Bacon",
    "Sausage", "Shrimp", "Salmon", "Tofu", "Chickpeas",
]

TAG_POOL = [
    "vegan", "vegetarian", "gluten-free", "spicy", "quick", "dessert",
    "breakfast", "dinner", "healthy", "comfort-food", "low-carb",
    "high-protein", "one-pot", "kid-friendly",
]


class Command(BaseCommand):
    help = "Seeds the database with fake users, recipes, reviews, and shopping-list data."

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=15, help="Number of users to create (default: 15).")
        parser.add_argument("--recipes", type=int, default=40, help="Number of recipes to create (default: 40).")
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing seed data (non-staff users and all their data, plus the catalog) before seeding.",
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            if options["clear"]:
                self._clear()

            fake = Faker()

            self._seed_catalog()
            users = self._seed_users(options["users"], fake)
            recipes = self._seed_recipes(options["recipes"], users, fake)
            reviews = self._seed_reviews(recipes, users, fake)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {len(users)} users, {len(recipes)} recipes, {len(reviews)} reviews. "
                    f"Password for all seeded users: {SEED_PASSWORD}"
                )
            )

    def _clear(self):
        deleted_users, _ = User.objects.filter(is_staff=False, is_superuser=False).delete()
        Ingredient.objects.all().delete()
        Tag.objects.all().delete()
        self.stdout.write(self.style.WARNING(f"Cleared {deleted_users} non-staff users and all catalog data."))

    def _seed_catalog(self):
        for name in INGREDIENT_POOL:
            get_or_create_ci(Ingredient, name)
        for name in TAG_POOL:
            get_or_create_ci(Tag, name)

    def _seed_users(self, count, fake):
        existing_usernames = set(User.objects.values_list("username", flat=True))
        hashed_password = make_password(SEED_PASSWORD)
        new_users = []
        for _ in range(count):
            username = fake.unique.user_name()
            while username in existing_usernames:
                username = fake.unique.user_name()
            existing_usernames.add(username)
            new_users.append(User(username=username, email=fake.unique.email(), password=hashed_password))
        return User.objects.bulk_create(new_users)

    def _seed_recipes(self, count, users, fake):
        if not users:
            return []
        units = [choice[0] for choice in RecipeIngredient.UNIT_CHOICES]
        ingredients = list(Ingredient.objects.all())
        tags = list(Tag.objects.all())

        new_recipes = [
            Recipe(
                name=fake.sentence(nb_words=3).rstrip("."),
                steps=[fake.sentence(nb_words=6) for _ in range(random.randint(3, 6))],
                owner=random.choice(users),
            )
            for _ in range(count)
        ]
        recipes = Recipe.objects.bulk_create(new_recipes)

        new_ingredient_rows = []
        new_tag_rows = []
        for recipe in recipes:
            recipe_ingredients = random.sample(ingredients, k=min(len(ingredients), random.randint(1, 8)))
            for order, ingredient in enumerate(recipe_ingredients):
                new_ingredient_rows.append(
                    RecipeIngredient(
                        recipe=recipe,
                        ingredient=ingredient,
                        amount=Decimal(random.randint(50, 500)) / 100,
                        unit=random.choice(units),
                        order=order,
                    )
                )
            recipe_tags = random.sample(tags, k=min(len(tags), random.randint(0, RecipeTag.MAX_TAGS)))
            for order, tag in enumerate(recipe_tags):
                new_tag_rows.append(RecipeTag(recipe=recipe, tag=tag, order=order))

        RecipeIngredient.objects.bulk_create(new_ingredient_rows)
        RecipeTag.objects.bulk_create(new_tag_rows)
        return recipes

    def _seed_reviews(self, recipes, users, fake):
        new_reviews = []
        for recipe in recipes:
            candidates = [user for user in users if user.pk != recipe.owner_id]
            if not candidates:
                continue
            reviewers = random.sample(candidates, k=min(len(candidates), random.randint(0, 5)))
            for reviewer in reviewers:
                new_reviews.append(
                    Review(
                        recipe=recipe,
                        user=reviewer,
                        rating=random.randint(1, 5),
                        comment=fake.sentence(nb_words=10),
                    )
                )
        return Review.objects.bulk_create(new_reviews)
