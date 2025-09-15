from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from propylon_document_manager.file_versions.api.views import FileVersionViewSet, DocumentView, DocumentListView, \
    DocumentByHashView

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

router.register("file_versions", FileVersionViewSet)

app_name = "api"
urlpatterns = router.urls + [
    path("documents/", DocumentListView.as_view(), name="document-list"),
    path("documents/hash/<str:content_hash>/", DocumentByHashView.as_view(), name="document-by-hash"),
    path("documents/<path:url>/", DocumentView.as_view(), name="document"),
]
