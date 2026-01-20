import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

User = get_user_model()


@pytest.mark.django_db
class TestUserEmailUniquenessConstraint:
    def test_allows_multiple_empty_emails(self):
        User.objects.create(username="user1", email="")
        User.objects.create(username="user2", email="")

        assert User.objects.filter(email="").count() == 2

    def test_allows_single_non_empty_email(self):
        User.objects.create(username="user1", email="test@example.com")

        assert User.objects.filter(email="test@example.com").count() == 1

    def test_forbids_duplicate_non_empty_email(self):
        User.objects.create(username="user1", email="dup@example.com")

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                User.objects.create(username="user2", email="dup@example.com")
