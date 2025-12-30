from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from account.models import Student, StudentRegistrationToken
from account.services import build_password_reset_link
from sesame.utils import get_token

from .factories import GroupFactory, OwnerFactory, StudentFactory, UserFactory


class AccountAPITests(APITestCase):
    @pytest.mark.django_db
    def test_owner_list_view(self):
        OwnerFactory.create_batch(5)
        response = self.client.get(reverse("owner-list"))
        assert response.status_code == 200
        assert len(response.json()) == 5

    @patch("sib_api_v3_sdk.TransactionalEmailsApi.send_transac_email")
    def test_request_magic_link(self, mock_send_email):
        mock_send_email.return_value = None

        response = self.client.post(reverse("request-magic-link"), {"email": "test@test.com"})
        assert response.status_code == 200
        assert response.json() == {
            "detail": "Si un compte existe avec cette adresse e-mail, vous recevrez un lien pour vous connecter. Veuillez contacter xxx en cas de problème."
        }

        UserFactory.create(email="test@test.com")
        response = self.client.post(reverse("request-magic-link"), {"email": "test@test.com"})
        assert response.status_code == 200
        assert response.json() == {
            "detail": "Si un compte existe avec cette adresse e-mail, vous recevrez un lien pour vous connecter. Veuillez contacter xxx en cas de problème."
        }
        assert mock_send_email.call_count == 1


class VerifyMagicLinkAPITests(APITestCase):
    def test_verify_magic_link_success_staff(self):
        user = UserFactory(is_active=True, is_staff=True, is_superuser=True)
        token = get_token(user)

        url = reverse("check-magic-link")
        response = self.client.post(url, {"sesame": token})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.assertEqual(data["user"]["role"], "admin")

    def test_verify_magic_link_success_owner(self):
        user = UserFactory(is_active=True, is_staff=False)
        owner_group = GroupFactory(name="Owners")
        user.groups.add(owner_group)
        OwnerFactory(users=[user])

        token = get_token(user)

        url = reverse("check-magic-link")
        response = self.client.post(url, {"sesame": token})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user"]["role"], "owner")
        self.assertEqual(data["user"]["email"], user.email)
        self.assertEqual(data["user"]["first_name"], user.first_name)
        self.assertEqual(data["user"]["last_name"], user.last_name)
        self.assertNotIn("password", data["user"])

    def test_verify_magic_link_success_user(self):
        user = UserFactory(is_active=True, is_staff=False)
        token = get_token(user)

        url = reverse("check-magic-link")
        response = self.client.post(url, {"sesame": token})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user"]["role"], "user")

    def test_verify_magic_link_invalid(self):
        url = reverse("check-magic-link")
        response = self.client.post(url, {"sesame": "invalidtoken"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invalid or expired token.")

    def test_verify_magic_link_missing_token(self):
        url = reverse("check-magic-link")
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Token is required.")


class TokenRefreshAPITests(APITestCase):
    def test_token_refresh_success(self):
        user = UserFactory(is_active=True, is_staff=True)
        refresh = RefreshToken.for_user(user)

        url = reverse("refresh-token")
        response = self.client.post(url, {"refresh": str(refresh)})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("access", data)
        self.assertNotEqual(str(refresh.access_token), data["access"])

    def test_token_refresh_invalid(self):
        url = reverse("refresh-token")
        response = self.client.post(url, {"refresh": "invalid_token"})
        self.assertEqual(response.status_code, 401)


class LogoutAPITests(APITestCase):
    def setUp(self):
        self.user = UserFactory(is_active=True, is_staff=True)
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.refresh_token = str(refresh)

        self.logout_url = reverse("logout")

    def test_logout_success(self):
        response = self.client.post(
            self.logout_url,
            {"refresh": self.refresh_token},
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["detail"], "Logout successful.")

        response2 = self.client.post(reverse("refresh-token"), {"refresh": self.refresh_token})
        self.assertEqual(response2.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("token_not_valid", response2.json().get("code", ""))

    def test_logout_invalid_token(self):
        response = self.client.post(
            self.logout_url, {"refresh": "invalidtoken"}, HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["detail"], "Invalid token.")

    def test_logout_without_auth(self):
        response = self.client.post(self.logout_url, {"refresh": self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class StudentRegistrationAPITests(APITestCase):
    @patch("sib_api_v3_sdk.TransactionalEmailsApi.send_transac_email")
    def test_student_registration_success(self, mock_send_email):
        mock_send_email.return_value = None

        response = self.client.post(
            reverse("student-register"),
            {"email": "test@test.com", "first_name": "Test", "last_name": "Test", "password": "testpassword"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["message"], "Student registered successfully")
        assert mock_send_email.call_count == 1
        student = Student.objects.get(user__email="test@test.com")
        self.assertEqual(student.user.first_name, "Test")
        self.assertEqual(student.user.last_name, "Test")
        self.assertEqual(student.user.is_active, False)
        self.assertEqual(student.user.is_staff, False)
        self.assertEqual(student.user.is_superuser, False)

        self.assertTrue(StudentRegistrationToken.objects.filter(student=student).exists())


class StudentRegistrationValidationAPITests(APITestCase):
    def test_student_registration_validation_success(self):
        student = StudentFactory.create(user__is_active=False, user__is_staff=False, user__is_superuser=False)
        token = StudentRegistrationToken.get_or_create_for_user(student.user)
        response = self.client.post(reverse("student-validate"), {"validation_token": token.token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Student validated successfully")

        student.refresh_from_db()
        self.assertEqual(student.user.is_active, True)
        self.assertEqual(student.user.is_staff, False)
        self.assertEqual(student.user.is_superuser, False)
        self.assertFalse(StudentRegistrationToken.objects.filter(student=student).exists())

    def test_student_registration_validation_invalid_token(self):
        response = self.client.post(reverse("student-validate"), {"validation_token": "invalidtoken"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["detail"], "Invalid or expired validation token")

    def test_student_registration_validation_already_validated(self):
        student = StudentFactory.create(user__is_active=True, user__is_staff=False, user__is_superuser=False)
        token = StudentRegistrationToken.get_or_create_for_user(student.user)
        response = self.client.post(reverse("student-validate"), {"validation_token": token.token})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["detail"], "Student already validated")


class StudentGetTokenAPITests(APITestCase):
    def test_student_get_token_success(self):
        student = StudentFactory.create(user__is_active=True, user__is_staff=False, user__is_superuser=False)
        student.user.set_password("testpassword")
        student.user.save()
        response = self.client.post(reverse("student-token"), {"email": student.user.email, "password": "testpassword"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("access", data)
        self.assertIn("refresh", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], student.user.email)
        self.assertEqual(data["user"]["first_name"], student.user.first_name)
        self.assertEqual(data["user"]["last_name"], student.user.last_name)
        self.assertNotIn("password", data["user"])

    def test_student_get_token_invalid_credentials(self):
        student = StudentFactory.create(user__is_active=True, user__is_staff=False, user__is_superuser=False)
        response = self.client.post(
            reverse("student-token"), {"email": student.user.email, "password": "invalidpassword"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["detail"], "Invalid email or password.")
        self.assertEqual(response.json()["type"], "invalid_email_or_password")


class StudentRequestPasswordResetAPITests(APITestCase):
    @patch("sib_api_v3_sdk.TransactionalEmailsApi.send_transac_email")
    def test_student_request_password_reset_success(self, mock_send_email):
        mock_send_email.return_value = None

        student = StudentFactory.create(user__is_active=True, user__is_staff=False, user__is_superuser=False)
        response = self.client.post(reverse("student-request-password-reset"), {"email": student.user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Password reset email sent if user exists")
        assert mock_send_email.call_count == 1

    @patch("sib_api_v3_sdk.TransactionalEmailsApi.send_transac_email")
    def test_student_request_password_reset_invalid_email(self, mock_send_email):
        mock_send_email.return_value = None

        response = self.client.post(reverse("student-request-password-reset"), {"email": "invalidemail@test.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Password reset email sent if user exists")
        assert mock_send_email.call_count == 0


class StudentPasswordResetConfirmAPITests(APITestCase):
    def test_student_password_reset_confirm_success(self):
        student = StudentFactory.create(user__is_active=True, user__is_staff=False, user__is_superuser=False)
        link = build_password_reset_link(student.user, "https://www.example.com")
        uid = link.split("uid=")[1].split("&")[0]
        token = link.split("token=")[1]
        response = self.client.post(
            reverse("student-password-reset-confirm", args=[uid, token]), {"new_password": "testpassword"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Password reset successfully")
        student.refresh_from_db()
        self.assertTrue(student.user.check_password("testpassword"))

    def test_student_password_reset_confirm_invalid_token(self):
        student = StudentFactory.create(user__is_active=True, user__is_staff=False, user__is_superuser=False)
        link = build_password_reset_link(student.user, "https://www.example.com")
        uid = link.split("uid=")[1].split("&")[0]
        response = self.client.post(
            reverse("student-password-reset-confirm", args=[uid, "invalidtoken"]), {"new_password": "testpassword"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["detail"], "Invalid reset link")
        self.assertEqual(response.json()["type"], "invalid_reset_link")

    def test_student_password_reset_confirm_invalid_uid(self):
        response = self.client.post(
            reverse("student-password-reset-confirm", args=["invaliduid", "validtoken"]),
            {"new_password": "testpassword"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["detail"], "Invalid reset link")
        self.assertEqual(response.json()["type"], "invalid_reset_link")


class StudentLogoutAPITests(APITestCase):
    def test_student_logout_success(self):
        student = StudentFactory.create(user__is_active=True, user__is_staff=False, user__is_superuser=False)
        refresh = RefreshToken.for_user(student.user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        response = self.client.post(
            reverse("student-logout"), {"refresh": refresh_token}, HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["message"], "Logout successfully")
        with self.assertRaises(TokenError):
            refresh.verify()

    def test_student_logout_invalid_token(self):
        response = self.client.post(reverse("student-logout"), {"refresh": "invalidtoken"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["detail"], "Invalid token.")
        self.assertEqual(response.json()["type"], "invalid_token")
