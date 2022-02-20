from django.contrib import admin
from django.http import HttpResponse

from .models import Airport
from .models import Metar
from .models import Answer
from .models import Question
from .models import Report

import os
import json


@admin.action(description='Download selected as JSON')
def download_reports_json(modeladmin, request, queryset):
    json_path = os.path.join(os.getcwd(), 'report_data.json')
    reports_data = []

    for item in queryset:
        answers_sub_data = []
        for answer in item.question.answers.all():
            answers_sub_data.append(answer.text)
        reports_data.append({'aiport_name': item.question.metar.airport.name,
                             'aiport_city': item.question.metar.airport.city,
                             'aiport_country': item.question.metar.airport.country,
                             'aiport_icao': item.question.metar.airport.icao,
                             'aiport_latitude': item.question.metar.airport.latitude,
                             'aiport_longitude': item.question.metar.airport.longitude,
                             'question_metar': json.loads(item.question.metar.metar_json),
                             'question_text': item.question.text,
                             'question_answers': answers_sub_data,
                             'question_category': item.question.category,
                             'report_description': item.description.replace('\n', ' ').replace('\r', ' ')})

    with open(json_path, 'w') as f:
        json.dump(reports_data, f)

    with open(json_path, 'r') as f:
        response = HttpResponse(f, content_type='text/json')
        response['Content-Disposition'] = 'attachment; filename=report_data.json'
        os.remove(json_path)
        return response



class AirportAdmim(admin.ModelAdmin):
    list_display = ['pk', 'name', 'city', 'country', 'icao', 'latitude', 'longitude']


class MetarAdmim(admin.ModelAdmin):
    list_display = ['pk', 'metar_json', 'airport']


class AnswerAdmim(admin.ModelAdmin):
    list_display = ['pk', 'text']


class QuestionAdmim(admin.ModelAdmin):
    list_display = ['pk', 'text', 'category', 'metar']


class ReportAdmim(admin.ModelAdmin):
    list_display = ['question', 'description']
    actions = [download_reports_json]



admin.site.register(Airport, AirportAdmim)
admin.site.register(Metar, MetarAdmim)
admin.site.register(Answer, AnswerAdmim)
admin.site.register(Question, QuestionAdmim)
admin.site.register(Report, ReportAdmim)
