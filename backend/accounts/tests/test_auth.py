import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_register_creates_user_and_logs_in():
    client = APIClient()
    response = client.post(
        "/api/auth/register/",
        {"username": "newchef", "email": "chef@example.com", "password": "a-strong-password-1"},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["username"] == "newchef"
    assert "_auth_user_id" in client.session


def test_register_rejects_duplicate_username():
    User.objects.create_user(username="dupe", email="dupe@example.com", password="a-strong-password-1")
    client = APIClient()
    response = client.post(
        "/api/auth/register/",
        {"username": "dupe", "email": "other@example.com", "password": "a-strong-password-1"},
        format="json",
    )
    assert response.status_code == 400
    assert response.data["code"] == "validation_error"
    assert "username" in response.data["errors"]


def test_login_succeeds_with_correct_credentials():
    User.objects.create_user(username="chef2", password="a-strong-password-1")
    client = APIClient()
    response = client.post(
        "/api/auth/login/", {"username": "chef2", "password": "a-strong-password-1"}, format="json"
    )
    assert response.status_code == 200
    assert response.data["username"] == "chef2"


def test_login_rejects_bad_credentials_with_generic_message():
    User.objects.create_user(username="chef3", password="a-strong-password-1")
    client = APIClient()
    response = client.post(
        "/api/auth/login/", {"username": "chef3", "password": "wrong-password"}, format="json"
    )
    assert response.status_code == 401
    assert response.data["code"] == "authentication_failed"
    assert response.data["detail"] == "Invalid credentials."


def test_logout_clears_session():
    User.objects.create_user(username="chef4", password="a-strong-password-1")
    client = APIClient()
    client.post("/api/auth/login/", {"username": "chef4", "password": "a-strong-password-1"}, format="json")
    assert "_auth_user_id" in client.session

    response = client.post("/api/auth/logout/")
    assert response.status_code == 200
    assert "_auth_user_id" not in client.session


def test_csrf_endpoint_sets_cookie():
    client = APIClient(enforce_csrf_checks=True)
    response = client.get("/api/auth/csrf/")
    assert response.status_code == 200
    assert "csrftoken" in response.cookies


def test_login_requires_csrf_token_for_real_browser_requests():
    from rest_framework.test import APIClient

    User.objects.create_user(username="chef5", password="a-strong-password-1")
    strict_client = APIClient(enforce_csrf_checks=True)
    strict_client.get("/api/auth/csrf/")  # sets the cookie but we deliberately don't echo it
    response = strict_client.post(
        "/api/auth/login/", {"username": "chef5", "password": "a-strong-password-1"}, format="json"
    )
    assert response.status_code == 403


def test_register_requires_csrf_token_for_real_browser_requests():
    strict_client = APIClient(enforce_csrf_checks=True)
    strict_client.get("/api/auth/csrf/")  # sets the cookie but we deliberately don't echo it
    response = strict_client.post(
        "/api/auth/register/",
        {"username": "chef_csrf", "email": "chef_csrf@example.com", "password": "a-strong-password-1"},
        format="json",
    )
    assert response.status_code == 403


def test_me_returns_current_user_when_authenticated():
    user = User.objects.create_user(username="chef_me", password="a-strong-password-1")
    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get("/api/auth/me/")
    assert response.status_code == 200
    assert response.data["id"] == user.id
    assert response.data["username"] == "chef_me"


def test_me_requires_authentication():
    client = APIClient()
    response = client.get("/api/auth/me/")
    assert response.status_code == 401
