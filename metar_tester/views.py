from django.shortcuts import render, redirect
from django.forms.models import model_to_dict

from metar_tester.models import Airport

from metar_tester.metar_collector import MetarCollector
from metar_tester.question_collector import QuestionColllector

from metar_tester.forms import ReportForm

import random

# using for testing
import os
import json


def open_practice(request):

    def select_question(questions):
        question = random.choice(list(questions.items()))
        question_key = question[0]
        question_value = question[1]

        questions.pop(question_key, None)

        if question_key.startswith('cloud'):
            remove_cloud_type = '_'.join(question_key.split('_')[0:2:])
            to_remove = []
            for key, value in questions.items():
                if key.startswith(remove_cloud_type):
                    to_remove.append(key)
            [questions.pop(key, None) for key in to_remove]

        if question_key == 'wind_speed' and question_value.is_trick():
            questions.pop('wind_direction', None)
        elif question_key == 'wind_direction' and question_value.is_trick():
            questions.pop('wind_speed', None)

        return question_value

    status = None
    airport = None
    raw_metar = None
    questions = None

    try:
        status = request.session['status']
        airport = request.session['airport']
        raw_metar = request.session['raw_metar']
        questions = request.session['questions']

        if len(questions) == 0:                                # Ran out of qustions refresh
            raise Exception('Ran out of questions, need to regenerate')
    except Exception:
        metar_collector = MetarCollector()
        while True:
            airport = metar_collector.get_random_airport()
            status = None
            raw_metar = None
            questions = None

            if airport is not None:
                status, raw_metar = metar_collector.get_raw_metar(airport['icao'])
                if status == 503:
                    break

            if raw_metar is not None:
                question_colllector = QuestionColllector(raw_metar)
                questions = question_colllector.generate_questions()

            if questions is not None:
                break

    if status == 200:
        request.session['status'] = status
        request.session['airport'] = airport
        request.session['raw_metar'] = raw_metar
        request.session['questions'] = questions

        data = {
            'title' : 'METAR Practice',
            'airport' : airport,
            'raw_metar' : raw_metar,
            'question' : questions.pop(0),
            'report_form' : ReportForm()
        }
        return render(request, 'metar_tester/begin.html', data)
    elif status == 503:
        print('TODO implement page saying API is down')
    else:
        print('TODO implement page saying API error has occured')
