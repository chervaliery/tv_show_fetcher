from django.core.management.base import BaseCommand, CommandError
from backoffice.utils import get_shows


class Command(BaseCommand):
    help = 'Get shows'

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO("Running show update..."))
        try:
            get_shows()
            self.stdout.write(self.style.SUCCESS('Successfully fetch shows'))
        except Exception as exc:
            raise CommandError(f"{exc}") from exc
