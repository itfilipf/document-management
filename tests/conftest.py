import pytest
from rest_framework.test import APIClient
from .factories import UserFactory, DocumentFactory


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    pass


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    """Store uploaded files in a temporary directory during tests."""
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def api_client(user):
    """API client authenticated as the test user forwarded."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def document(user):
    """Single test document belonging to the user."""
    return DocumentFactory(user=user, url="docs/test.txt", version__version_number=0)
