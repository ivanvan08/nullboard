import pytest
from rest_framework import status

from forum.models import Board, Tag

pytestmark = pytest.mark.django_db

BOARDS_URL = "/api/v1/boards/"
TAGS_URL = "/api/v1/tags/"


def board_url(slug):
    return f"{BOARDS_URL}{slug}/"


def tag_url(slug):
    return f"{TAGS_URL}{slug}/"


def test_boards_are_publicly_readable(api_client, board):
    response = api_client.get(BOARDS_URL)

    assert response.status_code == status.HTTP_200_OK
    assert [item["slug"] for item in response.data] == [board.slug]


def test_create_board_without_token_is_unauthorized(api_client):
    response = api_client.post(
        BOARDS_URL, {"slug": "ctf", "title": "CTF", "description": "Tasks"}, format="json"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_board_as_regular_user_is_forbidden(auth_client):
    response = auth_client.post(
        BOARDS_URL, {"slug": "ctf", "title": "CTF", "description": "Tasks"}, format="json"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert not Board.objects.filter(slug="ctf").exists()


def test_create_board_as_admin_succeeds(admin_client):
    response = admin_client.post(
        BOARDS_URL, {"slug": "ctf", "title": "CTF", "description": "Tasks"}, format="json"
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert Board.objects.filter(slug="ctf").exists()


def test_create_board_with_duplicate_slug_conflicts(admin_client, board):
    response = admin_client.post(
        BOARDS_URL,
        {"slug": board.slug, "title": "Duplicate", "description": "Text"},
        format="json",
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert Board.objects.filter(slug=board.slug).count() == 1


def test_retrieve_board(api_client, board):
    response = api_client.get(board_url(board.slug))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["slug"] == board.slug
    assert response.data["thread_count"] == 0


def test_patch_board_as_regular_user_is_forbidden(auth_client, board):
    response = auth_client.patch(
        board_url(board.slug), {"title": "Renamed"}, format="json"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    board.refresh_from_db()
    assert board.title == "Security"


def test_patch_tag_as_regular_user_is_forbidden(auth_client, tag):
    response = auth_client.patch(tag_url(tag.slug), {"title": "Changed"}, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    tag.refresh_from_db()
    assert tag.title == "Malware"


def test_patch_tag_as_admin_updates_title(admin_client, tag):
    response = admin_client.patch(tag_url(tag.slug), {"title": "Malware analysis"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    tag.refresh_from_db()
    assert tag.title == "Malware analysis"


def test_delete_tag_in_use_conflicts(admin_client, tag, thread):
    response = admin_client.delete(tag_url(tag.slug))

    assert response.status_code == status.HTTP_409_CONFLICT
    assert Tag.objects.filter(slug=tag.slug).exists()


def test_delete_tag_as_regular_user_is_forbidden(auth_client, tag):
    response = auth_client.delete(tag_url(tag.slug))

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Tag.objects.filter(slug=tag.slug).exists()
