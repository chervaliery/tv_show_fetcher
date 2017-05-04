from django.db import models
from django.utils import timezone

class Show(models.Model):
    name = models.CharField(max_length=255)
    tst_id = models.IntegerField()

    def __unicode__(self):
        return "{0}".format(self.name)


class Season(models.Model):
    number = models.IntegerField()
    show = models.ForeignKey('Show')

    def __unicode__(self):
        return "{0} S{1:02d}".format(self.show.name, self.number)


class Episode(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField(default=timezone.now)
    number = models.IntegerField()
    season = models.ForeignKey('Season')
    tst_id = models.IntegerField()
    downloaded = models.BooleanField()
    watched = models.BooleanField()

    def __unicode__(self):
        return "{0}E{1:02d}".format(self.season, self.number)
