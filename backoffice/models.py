from django.db import models


class Show(models.Model):
    name = models.CharField(max_length=255)
    tst_id = models.IntegerField(primary_key=True)
    enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name}"


class Episode(models.Model):
    name = models.CharField(max_length=255, blank=True)
    date = models.DateField(null=True)
    number = models.IntegerField()
    show = models.ForeignKey('Show', on_delete=models.CASCADE)
    season = models.IntegerField()
    tst_id = models.IntegerField(primary_key=True)
    aired = models.BooleanField()
    downloaded = models.BooleanField(default=False)
    watched = models.BooleanField()

    def __str__(self):
        return f"{self.show.name} S{self.season:02d}E{self.number:02d}"
