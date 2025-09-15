import io

import pytest
from django.urls import reverse

from .factories import UserFactory, DocumentFactory


# -----------------------------
# Authentication tests ( Ensure that endpoints require authentication )
# -----------------------------
@pytest.mark.django_db
def test_document_list_requires_authentication(api_client):
    url = reverse("api:document-list")
    api_client.logout()
    response = api_client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_document_by_hash_requires_authentication(api_client, document):
    url = reverse("api:document-by-hash", args=[document.content_hash])
    api_client.logout()
    response = api_client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_document_upload_requires_authentication(api_client):
    url = reverse("api:document", kwargs={"url": "docs/new.txt"})
    api_client.logout()
    response = api_client.post(url, {"file": b"unauthenticated"}, format="multipart")
    assert response.status_code == 403


@pytest.mark.django_db
def test_document_download_latest_requires_authentication(api_client, document):
    url = reverse("api:document", kwargs={"url": document.url})
    api_client.logout()
    response = api_client.get(url)
    assert response.status_code == 403


# -----------------------------
# Documents list endpoint test
# -----------------------------

@pytest.mark.django_db
def test_document_list_returns_only_user_documents(api_client, user):
    other_user = UserFactory()
    DocumentFactory(user=other_user, url="docs/other.txt", version__file_name="other.txt")

    DocumentFactory(user=user, url="docs/mine.txt", version__file_name="mine.txt")

    url = reverse("api:document-list")
    response = api_client.get(url)

    assert response.status_code == 200
    urls = [doc["url"] for doc in response.data["results"]]
    assert "docs/mine.txt" in urls
    assert "docs/other.txt" not in urls


@pytest.mark.django_db
def test_document_list_user_with_revisions(api_client, user):
    # One URL with 2 revisions
    DocumentFactory(
        user=user,
        url="documents/reviews/review.pdf",
        version__file_name="review.pdf",
        version__version_number=0,
    )
    DocumentFactory(
        user=user,
        url="documents/reviews/review.pdf",
        version__file_name="review.pdf",
        version__version_number=1,
    )

    # Another URL with 1 revision
    DocumentFactory(
        user=user,
        url="documents/contracts/nda.docx",
        version__file_name="nda.docx",
        version__version_number=0,
    )

    url = reverse("api:document-list")
    response = api_client.get(url)

    assert response.status_code == 200

    # Results are inside pagination wrapper
    results = response.data["results"]

    urls = [doc["url"] for doc in results]
    assert "documents/reviews/review.pdf" in urls
    assert "documents/contracts/nda.docx" in urls

    for doc in results:
        if doc["url"] == "documents/reviews/review.pdf":
            assert len(doc["revisions"]) == 2
            assert all(rev["file_name"] == "review.pdf" for rev in doc["revisions"])
        if doc["url"] == "documents/contracts/nda.docx":
            assert len(doc["revisions"]) == 1
            assert doc["revisions"][0]["file_name"] == "nda.docx"


# -----------------------------
# Retrieve document by hash tests
# -----------------------------

@pytest.mark.django_db
def test_document_by_hash(api_client, user):
    # Ensure the document belongs to this user
    doc = DocumentFactory(user=user, url="docs/mine.txt", version__file_name="mine.txt")

    url = reverse("api:document-by-hash", args=[doc.content_hash])
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.get("Content-Disposition").endswith(f"{doc.version.file_name}\"")

    # Document of another user should NOT be accessible
    other_user = UserFactory()
    other_doc = DocumentFactory(user=other_user, url="docs/other.txt", version__file_name="other.txt")
    url_other = reverse("api:document-by-hash", args=[other_doc.content_hash])
    response_other = api_client.get(url_other)
    assert response_other.status_code == 404


# -----------------------------
# Upload document test
# -----------------------------

@pytest.mark.django_db
def test_document_upload(api_client, user):
    url = reverse("api:document", kwargs={"url": "docs/new.txt"})
    file_bytes = b"new content"
    response = api_client.post(url, {"file": io.BytesIO(file_bytes)}, format="multipart")

    assert response.status_code == 201
    assert response.data["url"] == "docs/new.txt"
    assert response.data["user"] == str(user)


# -----------------------------
# Revision retrieval tests
# -----------------------------

@pytest.mark.django_db
def test_document_download_latest_returns_highest_revision(api_client, user):
    doc0 = DocumentFactory(
        user=user,
        url="docs/versioned.txt",
        version__file_name="versioned_0.txt",
        version__version_number=0,
    )

    doc1 = DocumentFactory(
        user=user,
        url="docs/versioned.txt",
        version__file_name="versioned_1.txt",
        version__version_number=1,
    )

    # Call endpoint without ?revision -> should return v1 (latest)
    url = reverse("api:document", kwargs={"url": "docs/versioned.txt"})
    response = api_client.get(url)

    assert response.status_code == 200
    # Latest revision should be returned
    assert response.get("Content-Disposition").endswith(f"{doc1.version.file_name}\"")


@pytest.mark.django_db
def test_fetch_specific_revision(api_client, user):
    DocumentFactory(user=user, url="docs/file.txt", version__file_name="file.txt", version__version_number=0)
    DocumentFactory(user=user, url="docs/file.txt", version__file_name="file.txt", version__version_number=1)

    url = reverse("api:document", kwargs={"url": "docs/file.txt"})
    r0 = api_client.get(url + "?revision=0")
    r1 = api_client.get(url + "?revision=1")

    assert r0.status_code == 200
    assert r1.status_code == 200
