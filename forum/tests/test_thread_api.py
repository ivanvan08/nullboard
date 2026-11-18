import pytest
from rest_framework import status

from forum.models import Post, Thread

pytestmark = pytest.mark.django_db

THREADS_URL = "/api/v1/threads/"
LOGIN_URL = "/api/v1/auth/login/"


def thread_url(pk):
    return f"/api/v1/threads/{pk}/"


def posts_url(pk):
    return f"/api/v1/threads/{pk}/posts/"


def test_list_threads_is_public(api_client, thread):
    response = api_client.get(THREADS_URL)

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.data] == [thread.id]


def test_list_threads_rejects_unknown_ordering(api_client, thread):
    response = api_client.get(THREADS_URL, {"ordering": "password"})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "ordering" in response.data["fields"]


def test_retrieve_thread_returns_tags_and_reply_count(api_client, thread):
    response = api_client.get(thread_url(thread.id))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["subject"] == thread.subject
    assert response.data["tags"] == ["malware"]
    assert response.data["reply_count"] == 0


def test_retrieve_unknown_thread_returns_404(api_client):
    response = api_client.get(thread_url(999999))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "message" in response.data


def test_create_thread_without_token_is_unauthorized(api_client, board):
    response = api_client.post(
        THREADS_URL,
        {"board": board.slug, "subject": "New", "body": "Text"},
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_thread_with_valid_token(auth_client, board, tag):
    response = auth_client.post(
        THREADS_URL,
        {
            "board": board.slug,
            "subject": "New thread",
            "body": "First post body",
            "name": "anon",
            "tags": [tag.slug],
        },
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["subject"] == "New thread"
    assert response.data["tags"] == [tag.slug]
    assert Thread.objects.filter(subject="New thread").exists()


def test_create_thread_with_invalid_data_returns_field_errors(auth_client, board):
    response = auth_client.post(
        THREADS_URL,
        {"board": board.slug, "subject": "", "body": ""},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert set(response.data["fields"]) >= {"subject", "body"}


def test_create_thread_on_unknown_board_fails(auth_client):
    response = auth_client.post(
        THREADS_URL,
        {"board": "no-such-board", "subject": "New", "body": "Text"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "board" in response.data["fields"]


def test_patch_thread_updates_subject(auth_client, thread):
    response = auth_client.patch(
        thread_url(thread.id), {"subject": "Edited subject"}, format="json"
    )

    assert response.status_code == status.HTTP_200_OK
    thread.refresh_from_db()
    assert thread.subject == "Edited subject"


def test_patch_thread_with_invalid_token_is_unauthorized(api_client, thread):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer not-a-real-token")
    response = api_client.patch(
        thread_url(thread.id), {"subject": "Hacked"}, format="json"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_thread_removes_it(auth_client, thread):
    response = auth_client.delete(thread_url(thread.id))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Thread.objects.filter(id=thread.id).exists()


def test_delete_unknown_thread_returns_404(auth_client):
    response = auth_client.delete(thread_url(999999))

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_reply_to_thread(auth_client, thread):
    response = auth_client.post(
        posts_url(thread.id), {"body": "A reply", "name": "anon"}, format="json"
    )

    assert response.status_code == status.HTTP_201_CREATED
    thread.refresh_from_db()
    assert thread.posts.count() == 1
    assert thread.bumped_at >= thread.created_at


def test_reply_to_locked_thread_conflicts(auth_client, locked_thread):
    response = auth_client.post(
        posts_url(locked_thread.id), {"body": "A reply"}, format="json"
    )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "locked" in response.data["message"].lower()
    assert locked_thread.posts.count() == 0


def test_reply_without_token_is_unauthorized(api_client, thread):
    response = api_client.post(posts_url(thread.id), {"body": "A reply"}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_with_wrong_password_is_unauthorized(api_client, user):
    response = api_client.post(
        LOGIN_URL, {"username": user.username, "password": "wrong-password"}, format="json"
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def post_url(pk):
    return f"/api/v1/posts/{pk}/"


def test_list_posts_of_thread(api_client, post):
    response = api_client.get(posts_url(post.thread_id))

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.data] == [post.id]


def test_retrieve_post(api_client, post):
    response = api_client.get(post_url(post.id))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["body"] == post.body


def test_retrieve_unknown_post_returns_404(api_client):
    response = api_client.get(post_url(999999))

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_patch_post_as_regular_user(auth_client, post):
    response = auth_client.patch(post_url(post.id), {"body": "Edited reply"}, format="json")

    assert response.status_code == status.HTTP_200_OK
    post.refresh_from_db()
    assert post.body == "Edited reply"


def test_patch_post_without_token_is_unauthorized(api_client, post):
    response = api_client.patch(post_url(post.id), {"body": "Edited reply"}, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_post(auth_client, post):
    response = auth_client.delete(post_url(post.id))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Post.objects.filter(id=post.id).exists()
