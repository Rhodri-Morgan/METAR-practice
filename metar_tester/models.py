from django.db import models


class Airport(models.Model):
    name = models.CharField(max_length=120)
    city = models.CharField(max_length=120)
    country = models.CharField(max_length=120)
    icao = models.CharField(max_length=4)
    latitude = models.CharField(max_length=120)
    longitude = models.CharField(max_length=120)


class Metar(models.Model):
    metar_json = models.TextField()                                             # Note JSON representation
    airport = models.ForeignKey(Airport, on_delete=models.PROTECT)


class Answer(models.Model):
    text = models.CharField(max_length=120)


class Question(models.Model):
    metar = models.ForeignKey(Metar, on_delete=models.PROTECT)
    text = models.CharField(max_length=120)
    answers = models.ManyToManyField(Answer)


class Report(models.Model):
    description = models.TextField(null=False)
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
