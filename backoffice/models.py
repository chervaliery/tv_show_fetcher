from django.db import models
from django.utils import timezone


class Show(models.Model):
    name = models.CharField(max_length=255)
    tst_id = models.IntegerField(primary_key=True)
    enabled = models.BooleanField()

    def __unicode__(self):
        return "{0}".format(self.name)


class Episode(models.Model):
    name = models.CharField(max_length=255, blank=True)
    date = models.DateField(default=timezone.now, blank=True)
    number = models.IntegerField()
    show = models.ForeignKey('Show', on_delete=models.CASCADE)
    season = models.IntegerField()
    tst_id = models.IntegerField(primary_key=True)
    aired = models.BooleanField()
    downloaded = models.BooleanField()
    watched = models.BooleanField()
    path = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return "{0} S{1:02d}E{2:02d}".format(self.show.name, self.season, self.number)
