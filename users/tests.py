from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


class UsersAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.regular_user = User.objects.create_user(
            username="normaluser",
            email="normal@example.com",
            password="StrongPassword123!",
            first_name="Ivan",
            last_name="Ivanov",
        )
        self.admin_user = User.objects.create_superuser(
            username="adminuser",
            email="admin@example.com",
            password="AdminPassword123!",
        )

    def test_registration_success(self):
        data = {
            "username": "newbie",
            "email": "newbie@example.com",
            "password": "Password789!",
            "password_confirmation": "Password789!",
            "first_name": "New",
            "last_name": "User",
        }
        response = self.client.post("/api/v1/auth/register/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["username"], "newbie")
        self.assertEqual(response.data["user"]["email"], "newbie@example.com")
        self.assertTrue(User.objects.filter(username="newbie").exists())

    def test_registration_password_mismatch(self):
        data = {
            "username": "mismatch",
            "email": "mismatch@example.com",
            "password": "Password789!",
            "password_confirmation": "DifferentPass789!",
        }
        response = self.client.post("/api/v1/auth/register/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password_confirmation", response.data["fields"])

    def test_registration_short_password(self):
        data = {
            "username": "shortpass",
            "email": "short@example.com",
            "password": "123",
            "password_confirmation": "123",
        }
        response = self.client.post("/api/v1/auth/register/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data["fields"])

    def test_login_success(self):
        data = {
            "username": "normaluser",
            "password": "StrongPassword123!",
        }
        response = self.client.post("/api/v1/auth/login/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid_credentials(self):
        data = {
            "username": "normaluser",
            "password": "WrongPassword!",
        }
        response = self.client.post("/api/v1/auth/login/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        refresh = RefreshToken.for_user(self.regular_user)
        response = self.client.post(
            "/api/v1/auth/refresh/",
            {"refresh": str(refresh)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_current_user_me(self):
        # Unauthenticated -> 401
        res = self.client.get("/api/v1/auth/me/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated -> 200
        self.client.force_authenticate(user=self.regular_user)
        res = self.client.get("/api/v1/auth/me/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["username"], "normaluser")


class ForumPermissionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="poster", password="StrongPassword123!"
        )
        self.admin = User.objects.create_superuser(
            username="admin", password="AdminPassword123!"
        )

    def test_public_can_read_boards_and_threads(self):
        res = self.client.get("/api/v1/boards/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        res = self.client.get("/api/v1/threads/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create_board(self):
        # Anonymous -> 401
        res = self.client.post(
            "/api/v1/boards/",
            {"slug": "test", "title": "Test", "description": "Desc"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # Regular authenticated user -> 403 Forbidden
        self.client.force_authenticate(user=self.user)
        res = self.client.post(
            "/api/v1/boards/",
            {"slug": "test", "title": "Test", "description": "Desc"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Admin -> 201 Created
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(
            "/api/v1/boards/",
            {"slug": "test", "title": "Test", "description": "Desc"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_thread_creation_requires_authentication(self):
        # Admin creates board first
        self.client.force_authenticate(user=self.admin)
        self.client.post(
            "/api/v1/boards/",
            {"slug": "tech", "title": "Tech", "description": "Tech board"},
            format="json",
        )

        # Anonymous tries to create thread -> 401
        self.client.force_authenticate(user=None)
        res = self.client.post(
            "/api/v1/threads/",
            {
                "board": "tech",
                "subject": "Anonymous Attempt",
                "body": "Should fail",
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authenticated user creates thread -> 201
        self.client.force_authenticate(user=self.user)
        res = self.client.post(
            "/api/v1/threads/",
            {
                "board": "tech",
                "subject": "User Thread",
                "body": "Should succeed",
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
