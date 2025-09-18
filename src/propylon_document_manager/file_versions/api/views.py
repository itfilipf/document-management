from django.shortcuts import render, get_object_or_404
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from ..models import FileVersion, Document, DocumentShare, User
from .serializers import FileVersionSerializer, DocumentWithRevisionsSerializer, DocumentSerializer
from rest_framework.response import Response
from django.http import FileResponse
from rest_framework import status
from ..pagination import StandardResultsSetPagination
from django.db import models, transaction
import hashlib


class FileVersionViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    authentication_classes = []
    permission_classes = []
    serializer_class = FileVersionSerializer
    queryset = FileVersion.objects.all()
    lookup_field = "id"


class DocumentView(APIView):
    """Handles upload (POST) and retrieval (GET) of documents by URL."""

    permission_classes = [IsAuthenticated]

    def post(self, request, url):
        user = request.user
        uploaded_file = request.FILES["file"]

        # Compute hash first
        hasher = hashlib.sha256()
        for chunk in uploaded_file.chunks():
            hasher.update(chunk)
        file_hash = hasher.hexdigest()

        # Check if any document with this hash already exists for same user & url
        if Document.objects.filter(user=user, url=url, content_hash=file_hash).exists():
            return Response(
                {"detail": "This file already exists for this URL (duplicate content)."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Determine next version number
        last_doc = (
            Document.objects.filter(user=user, url=url)
            .select_related("version")
            .order_by("-version__version_number")
            .first()
        )
        if last_doc:
            version_number = last_doc.version.version_number + 1
        else:
            version_number = 0

        # Create FileVersion
        file_version = FileVersion.objects.create(
            file_name=uploaded_file.name,
            version_number=version_number,
        )

        # Save Document
        document = Document.objects.create(
            user=user,
            url=url,
            file=uploaded_file,
            version=file_version,
            content_hash=file_hash,  # reuse computed hash
        )

        serializer = DocumentSerializer(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    def get(self, request, url):
        """Retrieve latest or specific revision of a document."""
        user = request.user
        revision = request.query_params.get("revision")

        qs = Document.objects.filter(user=user, url=url).select_related("version")

        if revision is not None:
            doc = get_object_or_404(qs, version__version_number=int(revision))
        else:
            doc = qs.order_by("-version__version_number").first()
            if not doc:
                return Response({"detail": "Not found"}, status=404)

        return FileResponse(doc.file, as_attachment=True, filename=doc.version.file_name)


class DocumentByHashView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, content_hash):
        user = request.user
        doc = (
            Document.objects
            .filter(content_hash=content_hash)
            .filter(models.Q(user=request.user) | models.Q(shares__shared_with=request.user))
            .first()
        )
        if not doc:
            return Response({"detail": "Not authorized"}, status=403)
        # Allow if owner or explicitly shared
        if doc.user != user and not DocumentShare.objects.filter(document=doc, shared_with=user).exists():
            return Response({"detail": "Not authorized"}, status=403)

        return FileResponse(doc.file, as_attachment=True, filename=doc.version.file_name)



class DocumentListView(APIView):
    """List all documents belonging to the authenticated user, with revisions (paginated)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        documents = Document.objects.filter(user=user).select_related("version")

        # Group by URL
        grouped = {}
        for doc in documents:
            grouped.setdefault(doc.url, []).append(doc)

        result = []
        for url, docs in grouped.items():
            serializer = DocumentWithRevisionsSerializer(
                {"url": url, "revisions": docs}
            )
            result.append(serializer.data)

        # Paginate the result list
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(result, request, view=self)
        return paginator.get_paginated_response(page)


class DocumentShareView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, content_hash):
        doc = get_object_or_404(Document, content_hash=content_hash, user=request.user)
        emails = request.data.get("emails", [])
        if not isinstance(emails, list):
            return Response({"detail": "emails must be a list"}, status=400)

        added, removed, not_found = [], [], []
        with transaction.atomic():
            current_shares = {s.shared_with.email: s for s in doc.shares.all()}

            for email in emails:
                try:
                    target_user = User.objects.get(email=email)
                    if email not in current_shares:
                        DocumentShare.objects.create(document=doc, shared_with=target_user)
                        added.append(email)
                except User.DoesNotExist:
                    not_found.append(email)

            for email, share in current_shares.items():
                if email not in emails:
                    share.delete()
                    removed.append(email)

        return Response({"added": added, "removed": removed, "not_found": not_found})
