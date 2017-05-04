from django.contrib import admin
from models import *

# Register your models here.

class EpisodeAdmin(admin.ModelAdmin):
    model = Episode
    list_display = ('id', 'name', 'get_show', 'get_season', 'downloaded', 'watched')
    list_filter = ('season__show__name', 'season__number', 'downloaded', 'watched')

    def get_season(self, obj):
        return obj.season.number

    def get_show(self, obj):
        return obj.season.show.name

    get_season.short_description = 'Season'
    get_show.short_description = 'Show'

admin.site.register(Show)
admin.site.register(Season)
admin.site.register(Episode, EpisodeAdmin)
