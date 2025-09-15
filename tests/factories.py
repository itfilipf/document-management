from django.core.files.base import ContentFile
from factory import Faker, post_generation, Sequence, SubFactory, lazy_attribute
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from propylon_document_manager.file_versions.models import FileVersion, Document
from datetime import datetime

User = get_user_model()


class UserFactory(DjangoModelFactory):
    email = Faker("email")
    name = Faker("name")

    @post_generation
    def password(self, create, extracted, **kwargs):
        password = extracted or Faker(
            "password",
            length=12,
            special_chars=True,
            digits=True,
            upper_case=True,
            lower_case=True,
        ).evaluate(None, None, extra={"locale": None})
        self.set_password(password)

    class Meta:
        model = User
        django_get_or_create = ["email"]

class FileVersionFactory(DjangoModelFactory):
    file_name = "default.txt"
    version_number = Sequence(lambda n: n)

    class Meta:
        model = FileVersion



class DocumentFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    url = Sequence(lambda n: f"docs/file{n}.txt")
    version = SubFactory(FileVersionFactory)

    @lazy_attribute
    def file(self):
        # Each file will contain a timestamp → unique content
        content = f"test content {datetime.utcnow().isoformat()}".encode()
        f = ContentFile(content)
        f.name = self.version.file_name
        return f

    class Meta:
        model = Document
