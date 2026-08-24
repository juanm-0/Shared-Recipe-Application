from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Review
from .services import recompute_rating_aggregate


@receiver(post_save, sender=Review)
def on_review_saved(sender, instance, **kwargs):
    recompute_rating_aggregate(instance.recipe_id)


@receiver(post_delete, sender=Review)
def on_review_deleted(sender, instance, **kwargs):
    recompute_rating_aggregate(instance.recipe_id)
