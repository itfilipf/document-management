from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from propylon_document_manager.file_versions.models import FileVersion, Document, DocumentShare

User = get_user_model()


class Command(BaseCommand):
    help = "Seed database with test users, documents and file versions"

    def handle(self, *args, **options):
        # Create users
        user1, _ = User.objects.get_or_create(email="alice@example.com", defaults={"name": "Alice"})
        user1.set_password("test1234")
        user1.save()

        user2, _ = User.objects.get_or_create(email="bob@example.com", defaults={"name": "Bob"})
        user2.set_password("test1234")
        user2.save()

        print("Users successfully created.")

        for user in [user1, user2]:
            url1 = "files/reviews/review.txt"

            fv0 = FileVersion.objects.create(file_name="review.txt", version_number=0)
            file0 = ContentFile(b"Revision 0 content")
            file0.name = "review.txt"
            Document.objects.create(user=user, url=url1, file=file0, version=fv0)

            fv1 = FileVersion.objects.create(file_name="review.txt", version_number=1)
            file1 = ContentFile(b"Revision 1 content")
            file1.name = "review.txt"
            Document.objects.create(user=user, url=url1, file=file1, version=fv1)

            # Second URL with a single revision
            url2 = "files/contracts/nda.txt"

            fv2 = FileVersion.objects.create(file_name="nda.txt", version_number=0)
            file2 = ContentFile(b"Contract NDA content")
            file2.name = "nda.txt"
            Document.objects.create(user=user, url=url2, file=file2, version=fv2)

            print(f"Documents successfully created for user {user.email}.")

        shared_doc = (
            Document.objects.filter(user=user1, url="files/reviews/review.txt")
            .order_by("-version__version_number")
            .first()
        )
        if shared_doc:
            DocumentShare.objects.get_or_create(document=shared_doc, shared_with=user2)
            print("Document successfully shared from Alice to Bob.")
