import pytest

from recipes.models import Tag
from recipes.utils import get_or_create_ci

pytestmark = pytest.mark.django_db


def test_get_or_create_ci_creates_when_missing():
    tag = get_or_create_ci(Tag, "Vegan")
    assert tag.name == "Vegan"
    assert Tag.objects.count() == 1


def test_get_or_create_ci_reuses_existing_case_insensitively():
    Tag.objects.create(name="Vegan")
    tag = get_or_create_ci(Tag, "vegan")
    assert tag.name == "Vegan"
    assert Tag.objects.count() == 1
