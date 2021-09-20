from django.db import models


class Airport(models.Model):
    """  Airport model used for storing details about airports """
    name = models.CharField(max_length=120)
    city = models.CharField(max_length=120)
    country = models.CharField(max_length=120)
    icao = models.CharField(max_length=4)
    latitude = models.CharField(max_length=120)
    longitude = models.CharField(max_length=120)


class Metar(models.Model):
    """  Metar model used for storing details about metar at connected airports """
    metar_json = models.TextField()                                             # Note JSON representation
    airport = models.ForeignKey(Airport, on_delete=models.PROTECT)


class Answer(models.Model):
    """  Answer model used for storing answer strings """
    text = models.CharField(max_length=120)


class Question(models.Model):
    """  Question model used for storing question strings and connecting them to answers """
    metar = models.ForeignKey(Metar, on_delete=models.PROTECT)
    text = models.CharField(max_length=120)
    answers = models.ManyToManyField(Answer)


class Report(models.Model):
    """  Report model used for storing question details and a users problem/issue """
    description = models.TextField(null=False)
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
