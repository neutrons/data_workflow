# taken from
# https://stackoverflow.com/questions/39744593/how-to-create-a-django-superuser-if-it-doesnt-exist-non-interactively
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Creates a non-admin user non-interactively if it doesn't exist"

    def add_arguments(self, parser):
        parser.add_argument("--username", help="User's username")
        parser.add_argument("--email", help="User's email")
        parser.add_argument("--password", help="User's password")

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(username=options["username"]).exists():
            User.objects.create_user(
                username=options["username"],
                email=options["email"],
                password=options["password"],
            )
