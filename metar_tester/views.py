from django.shortcuts import render, redirect
from django.forms.models import model_to_dict

from metar_tester.models import Airport

from metar_tester.metar_collector import METAR_colllector

import random

# using for testing
import os
import json


def begin_test(request):

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

        return question_value

    '''
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
        metar_collector = METAR_colllector()
        status, airport, raw_metar, questions = metar_collector.get_package()
        already_asked = []

    print(airport)

    if status == 200:
        print('TODO implement normal page')
    elif status == 503:
        print('TODO implement page saying API is down')
    else:
        print('TODO implement page saying API error has occured')
    '''

    # For purpose of testing above block commented out and using these known value
    metar_collector = METAR_colllector()
    sample_airport = model_to_dict(Airport.objects.get(icao="KJFK"))
    sample_raw_metar = None
    with open(os.path.join(os.getcwd(), 'metar_tester', 'sample_METAR.json')) as f:
        sample_raw_metar = json.loads(f.read())
    sample_questions = metar_collector.generate_questions(sample_raw_metar)
    sample_question = select_question(sample_questions)

    data = {
        'title' : 'METAR Tester - Begin',
        'airport' : sample_airport,
        'raw_metar' : sample_raw_metar,
        'question' : sample_question
    }
    return render(request, 'metar_tester/begin.html', data)
