from django.shortcuts import render, get_object_or_404
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from ..models import FileVersion, Document
from .serializers import FileVersionSerializer, DocumentWithRevisionsSerializer, DocumentSerializer
from rest_framework.response import Response
from django.http import FileResponse

from ..pagination import StandardResultsSetPagination


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
        """Upload a new document revision at the given URL."""
        user = request.user
        uploaded_file = request.FILES["file"]

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

        # Ensure file_name stays consistent
        file_version = FileVersion.objects.create(
            file_name=uploaded_file.name, version_number=version_number
        )

        # Save Document
        document = Document.objects.create(
            user=user,
            url=url,
            file=uploaded_file,
            version=file_version,
        )

        serializer = DocumentSerializer(document)
        return Response(serializer.data, status=201)

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
    """Retrieve a document by its content hash (CAS)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, content_hash):
        user = request.user
        doc = get_object_or_404(Document, user=user, content_hash=content_hash)
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
