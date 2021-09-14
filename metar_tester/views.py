from django.shortcuts import render, redirect
from django.forms.models import model_to_dict

from metar_tester.models import Airport
from metar_tester.models import Metar
from metar_tester.models import Question

from metar_tester.metar_collector import MetarCollector
from metar_tester.question_collector import QuestionColllector

from metar_tester.forms import ReportForm

import random
import json
import datetime


class ApiTimeoutError(Exception):
    pass


class RanOutOfQuestionsError(Exception):
    pass


def open_practice(request):

    def questions_to_dict(db_questions):
        questions = []
        for db_question in db_questions:
            question = model_to_dict(db_question)
            answers = []
            for db_answer in question['answers']:
                answers.append(model_to_dict(db_answer))
            question['answers'] = answers
            questions.append(question)
        return questions

    API_TIMEOUT_THRESHOLD = 10
    QUESTION_SAMPLE_COUNT = 5

    time_now = datetime.datetime.utcnow()

    status = None
    airport = None
    metar = None
    questions = None
    api = None

    try:
        status = request.session['status']
        airport = request.session['airport']
        metar = request.session['metar']
        questions = request.session['questions']
        api = request.session['api']

        print(api)

        if len(questions) == 0:
            raise RanOutOfQuestionsError('Ran out of questions, need to regenerate')
    except (RanOutOfQuestionsError, KeyError) as e:
        print(e)
        try:
            if api is not None and api['timeout'] == True and time_now < datetime.datetime.strptime(api['end_timeout'], '%m/%d/%Y, %H:%M:%S'):
                raise ApiTimeoutError('API is needing to timeout.')
            elif api is None:
                api = {'timeout' : False,
                       'end_timeout' : None}

            metar_collector = MetarCollector()
            timeout_counter = 0

            while True:
                status = None
                db_airport = metar_collector.get_random_airport()
                db_metar = None
                db_questions = None

                print(db_airport)
                print(db_airport.icao)

                if db_airport is not None:
                    status, db_metar = metar_collector.get_raw_metar(db_airport)

                print(status)
                print(db_metar)

                if status is None or status != 200:
                    timeout_counter += 1

                if db_metar is not None:
                    question_colllector = QuestionColllector(db_metar, QUESTION_SAMPLE_COUNT)
                    db_questions = question_colllector.generate_questions()
                    print(len(db_questions))
                    metar = question_colllector.metar
                    print(metar['station'])

                if db_questions is not None:
                    airport = model_to_dict(db_airport)
                    questions = questions_to_dict(db_questions)
                    break

                if timeout_counter == API_TIMEOUT_THRESHOLD:
                    end_timeout = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
                    api = {'timeout' : True,
                           'end_timeout' : end_timeout.strftime('%m/%d/%Y, %H:%M:%S')}
                    raise ApiTimeoutError('API is needing to timeout.')
        except ApiTimeoutError as e:
            while True:
                db_metar = Metar.objects.order_by('?').first()
                metar = json.loads(db_metar.metar_json)
                airport = model_to_dict(db_metar.airport)
                if status == None:
                    status = 400
                db_questions_all = Question.objects.filter(metar=db_metar)
                db_questions = None
                if len(db_questions_all) <= QUESTION_SAMPLE_COUNT:
                    db_questions = list(db_questions_all)
                else:
                    db_questions = random.sample(list(db_questions_all), k=QUESTION_SAMPLE_COUNT)
                questions = questions_to_dict(db_questions)
                if len(questions) >= 1:
                    break

    request.session['status'] = status
    request.session['airport'] = airport
    request.session['metar'] = metar
    request.session['questions'] = questions
    request.session['api'] = api

    data = {
        'title' : 'METAR Practice',
        'status' : status,
        'airport' : airport,
        'metar' : metar,
        'question' : questions.pop(0),
        'report_form' : ReportForm()
    }

    return render(request, 'metar_tester/begin.html', data)
