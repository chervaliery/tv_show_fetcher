from django.core.management.base import BaseCommand, CommandError
from backoffice.utils import download_episode
from backoffice.models import Episode

class Command(BaseCommand):
    help = 'Download episodes'

    def add_arguments(self, parser):
        parser.add_argument('episode_id', nargs='*', type=int)
        parser.add_argument(
            '--to-watch',
            action='store_true',
            dest='to-watch',
            default=False,
            help='Delete poll instead of closing it',
        )

    def handle(self, *args, **options):
        if options['to-watch']:
            episode_list = Episode.objects.filter(show__enabled=True, watched=False, downloaded=False, aired=True)
        else:
            episode_list = Episode.objects.filter(pk__in=options['episode_id'])
        download_episode(episode_list)
