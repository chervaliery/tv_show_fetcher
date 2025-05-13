from django.conf import settings
from django.core.cache import cache

from django.core.management.base import BaseCommand, CommandError

from shortener.views import refresh_oc_cache, refresh_share_cache, refresh_yourls_cache

import owncloud

class Command(BaseCommand):
    help = 'Refresh cache'

    def handle(self, *args, **options):
        refresh_yourls_cache()

        oc = owncloud.Client(settings.OC_SERVER)
        oc.login(settings.OC_USER, settings.OC_PASSWORD)

        list_of_files = self.get_files(oc, '/Local')
        cache.set(f"list_of_files-/Local", list_of_files)

        for file in list_of_files:
            refresh_share_cache(file)


    def get_files(self, oc, path, results=None):
        if results is None:
            results = []
        list_of_files = oc.list(path)
        for file in list_of_files:
            results.append(file)
            if file.is_dir():
                self.get_files(oc, file.get_path(), results)
        return results
