import random

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from recipes.models import Ingredient, Tag
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

            self.stdout.write(
                self.style.SUCCESS(
                    f"Created {len(users)} users. Password for all seeded users: {SEED_PASSWORD}"
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
