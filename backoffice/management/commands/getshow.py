from django.core.management.base import BaseCommand, CommandError
from backoffice.utils import get_show

class Command(BaseCommand):
    help = 'Get shows'

    def handle(self, *args, **options):
        get_show()
