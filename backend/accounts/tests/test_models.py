import pytest
from django.conf import settings
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db


def test_auth_user_model_points_at_custom_user():
    assert settings.AUTH_USER_MODEL == "accounts.User"


def test_user_can_be_created_and_authenticated():
    User = get_user_model()
    user = User.objects.create_user(username="chef", password="pw12345")
    assert user.pk is not None
    assert user.check_password("pw12345")
