from django.apps import apps as global_apps
from django.conf import settings
from django.contrib.auth.management import create_permissions
from django.db import migrations

MODERATED_MODELS = ["recipe", "tag", "ingredient", "review"]


def create_groups(apps, schema_editor):
    for app_config in global_apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    User = apps.get_model(settings.AUTH_USER_MODEL)

    admin_group, _ = Group.objects.get_or_create(name="Admin")
    Group.objects.get_or_create(name="User")

    codenames = [
        f"{action}_{model}"
        for model in MODERATED_MODELS
        for action in ("change", "delete")
    ]
    permissions = Permission.objects.filter(
        content_type__app_label="recipes", codename__in=codenames
    )
    admin_group.permissions.set(permissions)

    previously_privileged = User.objects.filter(is_staff=True, is_superuser=False)
    admin_group.user_set.add(*previously_privileged)


def remove_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=["Admin", "User"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0007_recipe_avg_rating_recipe_review_count_and_more"),
    ]

    operations = [
        migrations.RunPython(create_groups, remove_groups),
    ]
