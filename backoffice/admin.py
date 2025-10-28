import datetime
import json

from adminplus.sites import AdminSitePlus
from django.contrib import admin
from django.shortcuts import render, redirect
from django import forms

from .models import Show, Episode
from .utils import fetch_show, download_episode, download_by_urls, get_shows, print_messages

# Use AdminSitePlus instead of default admin
admin_site = AdminSitePlus(name='backoffice')
admin_site.site_header = "My Custom AdminPlus Dashboard"

# Custom Actions


@admin.action(description="Enable Shows")
def enable_show_action(modeladmin, request, queryset):
    queryset.update(enabled=True)


@admin.action(description="Disable Shows")
def disable_show_action(modeladmin, request, queryset):
    queryset.update(enabled=False)


@admin.action(description="Fetch Shows")
def fetch_show_action(modeladmin, request, queryset):
    for show in queryset.all():
        fetch_show(show)


@admin.action(description="Mark as Downloaded")
def mark_downloaded_action(modeladmin, request, queryset):
    queryset.update(downloaded=True)


@admin.action(description="Download Episodes")
def download_episodes_action(modeladmin, request, queryset):
    resp = download_episode(queryset.all())
    print_messages(request, resp)


# Admin Classes
class ShowAdmin(admin.ModelAdmin):
    model = Show
    list_display = ('tst_id', 'name', 'get_episode', 'get_to_watch', 'get_to_download', 'enabled')
    list_filter = ('name', 'enabled')
    actions = [enable_show_action, disable_show_action, fetch_show_action]

    def get_episode(self, obj):
        return len(obj.episode_set.all())
    get_episode.short_description = 'Number of Episode'

    def get_to_watch(self, obj):
        return len(obj.episode_set.filter(aired=True, watched=False))
    get_to_watch.short_description = 'Number to Watch'

    def get_to_download(self, obj):
        return len(obj.episode_set.filter(aired=True, watched=False, downloaded=False))
    get_to_download.short_description = 'Number to Download'


class EpisodeAdmin(admin.ModelAdmin):
    model = Episode
    list_display = ('tst_id', 'name', 'get_show', 'season', 'number', 'date', 'aired', 'watched', 'downloaded')
    list_filter = ('show__name', 'season', 'aired', 'downloaded', 'watched', 'show__enabled')
    ordering = ('-date',)
    actions = [download_episodes_action, mark_downloaded_action]

    def get_show(self, obj):
        return obj.show.name

    get_show.short_description = 'Show'

# Custom view


@admin_site.register_view('list_to_download', urlname='list_to_download', name='List the "to download" episodes')
def list_to_download_action(request):
    return redirect('/admin/backoffice/episode/?aired__exact=1&downloaded__exact=0&show__enabled__exact=1&watched__exact=0')


@admin_site.register_view('fetch_show', urlname='fetch_show', name='Fetch the enabled shows')
def fetch_show_action(request):
    for s in Show.objects.filter(enabled=True):
        fetch_show(s)
    return redirect('/admin')


@admin_site.register_view('get_show', urlname='get_show', name='Get the shows')
def get_show_action(request):
    get_shows()
    return redirect('/admin')


@admin_site.register_view('download_episode', urlname='download_episode', name='Download the "to download" episodes')
def download_episode_action(request):
    episode_list = Episode.objects.filter(
        show__enabled=True,
        watched=False,
        downloaded=False,
        aired=True,
        date__lte=datetime.date.today())
    resp = download_episode(episode_list)
    print_messages(request, resp)
    return redirect('/admin')


# ------------------------------
# Custom view with a form
# ------------------------------

# Define a simple form
class UrlListForm(forms.Form):
    urls = forms.CharField(widget=forms.HiddenInput(), required=False)


@admin_site.register_view('download-url/', 'Download by URL')
def download_url(request):
    if request.method == 'POST':
        form = UrlListForm(request.POST)
        if form.is_valid():
            try:
                urls = json.loads(form.cleaned_data["urls"]) or []
            except json.JSONDecodeError:
                urls = []

            resp = download_by_urls(urls)
            print_messages(request, resp)

            return render(request, 'admin/download_url.html', {'form': UrlListForm()})
    else:
        form = UrlListForm()

    return render(request, 'admin/download_url.html', {'form': form})


# Register Admin views
admin_site.register(Show, ShowAdmin)
admin_site.register(Episode, EpisodeAdmin)
