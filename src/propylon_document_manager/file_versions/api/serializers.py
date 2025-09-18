from rest_framework import serializers
from ..models import FileVersion, User, Document



class UserSerializer(serializers.ModelSerializer):
    """Basic serializer for User model."""

    class Meta:
        model = User
        fields = ["id", "email", "name"]


class FileVersionSerializer(serializers.ModelSerializer):
    """Serializer for FileVersion model."""

    class Meta:
        model = FileVersion
        fields = ["id", "file_name", "version_number"]


class DocumentRevisionSerializer(serializers.ModelSerializer):
    """Serializer for one revision of a document (e.g. v0, v1)."""

    version_number = serializers.IntegerField(source="version.version_number")
    file_name = serializers.CharField(source="version.file_name")
    shared_users = serializers.SerializerMethodField(read_only=True)


    class Meta:
        model = Document
        fields = [
            "id",
            "version_number",
            "file_name",
            "content_hash",
            "created_at",
            "shared_users"
        ]

    def get_shared_users(self, obj):
        return UserSerializer(
            [share.shared_with for share in obj.shares.all()],
            many=True
        ).data


class DocumentSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for a single Document instance (upload/retrieve).
    Includes user and version info.
    """

    user = serializers.StringRelatedField(read_only=True)  # shows email
    version = FileVersionSerializer(read_only=True)
    shared_users = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "url",
            "file",
            "content_hash",
            "version",
            "user",
            "created_at",
            "shared_users",
        ]
        read_only_fields = ["content_hash", "user", "created_at", "shared_users"]

    def get_shared_users(self, obj):
        return UserSerializer(
            [share.shared_with for share in obj.shares.all()],
            many=True
        ).data

class DocumentWithRevisionsSerializer(serializers.Serializer):
    """
    Serializer for grouping documents by URL and showing all their revisions.
    Example use: listing all user documents with all revisions.
    """

    url = serializers.CharField()
    revisions = DocumentRevisionSerializer(many=True)
