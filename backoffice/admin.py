from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

from backoffice.models import *
from backoffice.utils import fetch_show, get_show, download_episode

import datetime

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
    list_filter = ('show__name', 'season', 'aired', 'downloaded', 'watched', 'show__enabled')
    ordering = ('-date',)
    actions = [download_episodes, mark_downloaded]

    def get_show(self, obj):
        return obj.show.name

    get_show.short_description = 'Show'

# Custom view
@admin.site.register_view('list_to_download', urlname='list_to_download', name='List the "to download" episodes')
def list_to_download_action(request):
    return redirect('/admin/backoffice/episode/?aired__exact=1&downloaded__exact=0&show__enabled__exact=1&watched__exact=0')

@admin.site.register_view('fetch_show', urlname='fetch_show', name='Fetch the enabled shows')
def fetch_show_action(request):
    for s in Show.objects.filter(enabled=True):
        fetch_show(s)
    return redirect('/admin')

@admin.site.register_view('get_show', urlname='get_show', name='Get the shows')
def get_show_action(request):
    get_show()
    return redirect('/admin')

@admin.site.register_view('download_episode', urlname='download_episode', name='Download the "to download" episodes')
def download_episode_action(request):
    episode_list = Episode.objects.filter(show__enabled=True, watched=False, downloaded=False, aired=True, date__lte=datetime.date.today())
    res = download_episode(episode_list)
    messages.success(request, res)
    return redirect('/admin')

admin.site.register(Show, ShowAdmin)
admin.site.register(Episode, EpisodeAdmin)
