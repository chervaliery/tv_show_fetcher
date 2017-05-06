from django.contrib import admin
from django.contrib import messages
from models import *

from utils import fetch_show, get_show, download_episode

# Register your models here.

def mark_downloaded(modeladmin, request, queryset):
    queryset.update(downloaded=True)
mark_downloaded.short_description = "Mark as Downloaded"

def enable_show(modeladmin, request, queryset):
    queryset.update(enabled=True)
enable_show.short_description = "Enable Show"

def disable_show(modeladmin, request, queryset):
    queryset.update(enabled=False)
disable_show.short_description = "Disable Show"

def fetch_shows(modeladmin, request, queryset):
    for s in queryset.all():
        fetch_show(s)
fetch_shows.short_description = "Fetch Show"

def download_episodes(modeladmin, request, queryset):
    res = download_episode(queryset.all())
    messages.success(request, res)
download_episodes.short_description = "Download Episode"

class ShowAdmin(admin.ModelAdmin):
    model = Show
    list_display = ('tst_id', 'name', 'get_episode', 'get_to_watch', 'get_to_download', 'enabled')
    list_filter = ('name', 'enabled')
    actions = [enable_show, disable_show, fetch_shows]

    def get_episode(self, obj):
        return len(obj.episode_set.all())

    def get_to_watch(self, obj):
        return len(obj.episode_set.filter(aired=True, watched=False))

    def get_to_download(self, obj):
        return len(obj.episode_set.filter(aired=True, watched=False, downloaded=False))

class EpisodeAdmin(admin.ModelAdmin):
    model = Episode
    list_display = ('tst_id', 'name', 'get_show', 'season', 'number', 'date', 'aired', 'watched', 'downloaded')
    list_filter = ('show__name', 'season', 'aired', 'downloaded', 'watched')
    ordering = ('-date',)
    actions = [download_episodes, mark_downloaded]

    def get_show(self, obj):
        return obj.show.name

    get_show.short_description = 'Show'

admin.site.register(Show, ShowAdmin)
admin.site.register(Episode, EpisodeAdmin)
