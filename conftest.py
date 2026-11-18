import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from forum.models import Board, Post, Tag, Thread

User = get_user_model()

REGULAR_PASSWORD = "StrongPassword123!"
ADMIN_PASSWORD = "AdminPassword123!"


@pytest.fixture(scope="function")
def api_client():
    yield APIClient()


@pytest.fixture(scope="function")
def user(db):
    return User.objects.create_user(
        username="normaluser",
        email="normal@example.com",
        password=REGULAR_PASSWORD,
    )


@pytest.fixture(scope="function")
def admin(db):
    return User.objects.create_superuser(
        username="adminuser",
        email="admin@example.com",
        password=ADMIN_PASSWORD,
    )


def _login(api_client, username, password):
    response = api_client.post(
        "/api/v1/auth/login/",
        {"username": username, "password": password},
        format="json",
    )
    assert response.status_code == 200, response.data
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return api_client


@pytest.fixture(scope="function")
def auth_client(api_client, user):
    return _login(api_client, user.username, REGULAR_PASSWORD)


@pytest.fixture(scope="function")
def admin_client(api_client, admin):
    return _login(api_client, admin.username, ADMIN_PASSWORD)


@pytest.fixture(scope="function")
def board(db):
    return Board.objects.create(
        slug="sec",
        title="Security",
        description="Malware, exploits, defensive tooling",
    )


@pytest.fixture(scope="function")
def tag(db):
    return Tag.objects.create(slug="malware", title="Malware")


@pytest.fixture(scope="function")
def thread(board, tag):
    created = Thread.objects.create(
        board=board,
        name="anon",
        subject="Battery life on a ThinkPad",
        body="What do you use, tlp or auto-cpufreq?",
    )
    created.tags.add(tag)
    return created


@pytest.fixture(scope="function")
def locked_thread(board):
    return Thread.objects.create(
        board=board,
        name="anon",
        subject="Closed thread",
        body="No new replies here.",
        is_locked=True,
    )


@pytest.fixture(scope="function")
def post(thread):
    return Post.objects.create(
        thread=thread,
        name="anon",
        body="I use tlp, it works fine.",
    )
