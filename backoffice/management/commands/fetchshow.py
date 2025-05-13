from django.core.management.base import BaseCommand, CommandError
from backoffice.utils import fetch_show
from backoffice.models import Show

class Command(BaseCommand):
    help = 'Fetch Show'

    def add_arguments(self, parser):
        parser.add_argument('show_id', nargs='*', type=int)
        parser.add_argument(
            '--all',
            action='store_true',
            dest='all',
            default=False,
            help='Update all',
        )

        parser.add_argument(
            '--enabled',
            action='store_true',
            dest='enabled',
            default=False,
            help='Update enabled',
        )

    def handle(self, *args, **options):
        if options['all']:
            shows = Show.objects.all()
        elif options['enabled']:
            shows = Show.objects.filter(enabled=True)
        else:
            shows = Show.objects.filter(pk__in=options['show_id'])
        for show in shows:
            fetch_show(show)
