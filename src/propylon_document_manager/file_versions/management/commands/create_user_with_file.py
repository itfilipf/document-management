from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from propylon_document_manager.file_versions.models import FileVersion, Document

User = get_user_model()


class Command(BaseCommand):
    help = "Create a user with given email/password and create a document on the given URL."

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Email of the user to create or update")
        parser.add_argument("password", type=str, help="Password for the user")
        parser.add_argument("url", type=str, help="Document URL")

    def handle(self, *args, **options):
        email = options["email"]
        password = options["password"]
        url = options["url"]

        # Create or update user
        user, created = User.objects.get_or_create(email=email, defaults={"name": email.split("@")[0]})
        user.set_password(password)
        user.save()

        if created:
            print("User created successfully. ")
        else:
            print("User already exists. Password updated. ")

        existing_docs = Document.objects.filter(user=user, url=url).order_by("-version__version_number")
        if existing_docs.exists():
            next_version = existing_docs.first().version.version_number + 1
        else:
            next_version = 0

        # Create FileVersion and Document
        file_name = url.split("/")[-1]
        fv = FileVersion.objects.create(file_name=file_name, version_number=next_version)

        file_content = ContentFile(f"Revision {next_version} content".encode("utf-8"))
        file_content.name = file_name

        Document.objects.create(user=user, url=url, file=file_content, version=fv)

        print("Document created successfully. ")

