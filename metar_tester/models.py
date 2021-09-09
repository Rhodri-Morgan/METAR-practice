from django.db import models


class Report(models.Model):
    description = models.TextField(null=False)


class Airport(models.Model):
    name = models.CharField(max_length=120)
    city = models.CharField(max_length=120)
    country = models.CharField(max_length=120)
    icao = models.CharField(max_length=4)
    latitude = models.CharField(max_length=120)
    longitude = models.CharField(max_length=120)
