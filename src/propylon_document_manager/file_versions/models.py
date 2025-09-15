import hashlib

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField, EmailField
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Default custom user model for Propylon Document Manager.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def get_absolute_url(self) -> str:
        """Get URL for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"pk": self.id})


class FileVersion(models.Model):
    file_name = models.fields.CharField(max_length=512)
    version_number = models.fields.IntegerField()


class Document(models.Model):
    """
    Represents a single stored file (a revision of a logical document URL)
    belonging to a user.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    url = models.CharField(
        max_length=1024,
        help_text="Logical document URL chosen by the user",
    )
    file = models.FileField(
        upload_to="documents/",
        help_text="The actual uploaded file content",
    )
    content_hash = models.CharField(
        max_length=64,
        db_index=True,
    )
    version = models.ForeignKey(
        "FileVersion",
        on_delete=models.CASCADE,
        related_name="documents",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "url", "version")
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        # Compute content hash if not already set
        if self.file and not self.content_hash:
            hasher = hashlib.sha256()
            for chunk in self.file.chunks():
                hasher.update(chunk)
            self.content_hash = hasher.hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.url} (v{self.version.version_number}) - {self.user.email}"
