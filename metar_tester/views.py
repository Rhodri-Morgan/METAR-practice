from django.shortcuts import render, redirect
from django.forms.models import model_to_dict

from metar_tester.models import Airport

from metar_tester.metar_collector import MetarCollector
from metar_tester.question_collector import QuestionColllector

from metar_tester.forms import ReportForm

import random
import json


def open_practice(request):
    status = None
    airport = None
    metar = None
    questions = None

    try:
        status = request.session['status']
        airport = request.session['airport']
        metar = request.session['metar']
        questions = request.session['questions']

        if len(questions) == 0:
            raise Exception('Ran out of questions, need to regenerate')
    except Exception:
        metar_collector = MetarCollector()
        while True:
            status = None
            db_airport = metar_collector.get_random_airport()
            db_metar = None
            db_questions = None

            if db_airport is not None:
                status, db_metar = metar_collector.get_raw_metar(db_airport)
                if status == 503:
                    break

            if db_metar is not None:
                question_colllector = QuestionColllector(db_metar)
                db_questions = question_colllector.generate_questions()
                metar = question_colllector.metar

            if db_questions is not None:
                airport = model_to_dict(db_airport)
                questions = []
                for db_question in db_questions:
                    question = model_to_dict(db_question)
                    answers = []
                    for db_answer in question['answers']:
                        answers.append(model_to_dict(db_answer))
                    question['answers'] = answers
                    questions.append(question)
                break

    request.session['status'] = status
    request.session['airport'] = airport
    request.session['metar'] = metar
    request.session['questions'] = questions

    data = {
        'title' : 'METAR Practice',
        'status' : status,
        'airport' : airport,
        'metar' : metar,
        'question' : questions.pop(0),
        'report_form' : ReportForm()
    }

    if status == 200:
        print('Live data operating normally')
    elif status == 503:
        print('TODO implement page saying API is down')
    else:
        print('TODO implement page saying API error has occured')

    return render(request, 'metar_tester/begin.html', data)

'''
NEED TO MIGRATE, CHANGED FIELD NAME IN QUESTIONS
'''
