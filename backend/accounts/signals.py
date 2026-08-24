from django.contrib.auth.models import Group
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from .models import User


@receiver(m2m_changed, sender=User.groups.through)
def on_user_groups_changed(sender, instance, action, reverse, pk_set, **kwargs):
    if action != "post_add" or not pk_set:
        return

    if reverse:
        if instance.name == "Admin":
            User.objects.filter(pk__in=pk_set, is_staff=False).update(is_staff=True)
        return

    if Group.objects.filter(pk__in=pk_set, name="Admin").exists() and not instance.is_staff:
        instance.is_staff = True
        instance.save(update_fields=["is_staff"])
