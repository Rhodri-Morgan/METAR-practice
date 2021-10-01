from django.shortcuts import render, redirect
from django.forms.models import model_to_dict

from common.utils import get_url

from metar_practice.models import Airport
from metar_practice.models import Metar
from metar_practice.models import Question

from metar_practice.enums import QuestionType

from metar_practice.forms import ReportForm

from metar_practice.metar_collector import MetarCollector
from metar_practice.question_collector import QuestionCollector

import json


QUESTIONS_TRACEBACK_ALLOWED = 10


def metar_practice(request):
    """  Responsible for displaying user with data and handling reports made by user """
    previous_questions = []
    logged = None

    try:
        previous_questions = request.session['previous_questions']
        logged = request.session['logged']
    except KeyError as e:
        print(e)

    try:
        if request.method == 'POST':
            print(request.POST)
            report_form = ReportForm(request.POST)
            if report_form.is_valid() and len(previous_questions) >= 1:
                report = report_form.save(commit=False)
                report.question = Question.objects.get(id=previous_questions[0]['id'])
                report.full_clean()
                report.save()
                request.session['logged'] = 'Thank you. Your issue has been logged.'
                return redirect('metar_practice')
    except Question.DoesNotExist as e:
        print(e)

    airport = None
    metar = None
    question = None

    unwanted_question_types = [question['category'] for question in previous_questions]

    while True:
        db_question = Question.objects.order_by('?').first()
        if db_question.category not in unwanted_question_types:
            db_metar = db_question.metar
            db_airport = db_metar.airport
            metar = json.loads(db_metar.metar_json)
            airport = model_to_dict(db_metar.airport)
            question = model_to_dict(db_question)
            answers = []
            for db_answer in question['answers']:
                answers.append(model_to_dict(db_answer))
            question['answers'] = answers
            break

    previous_questions.append(question)
    while len(previous_questions) > QUESTIONS_TRACEBACK_ALLOWED:
        previous_questions.pop(0)

    request.session['previous_questions'] = previous_questions
    if logged is not None:
        request.session['logged'] = None
    else:
        request.session['logged'] = logged

    database_data = {'questions_count': len(Question.objects.all()), 'airports_count': len(Airport.objects.all())}

    data = {
        'title' : 'METAR Practice',
        'path' : get_url(request.path.split('/')[1:-1]),
        'logged' : logged,
        'database_data' : database_data,
        'airport' : airport,
        'metar' : metar,
        'question' : question,
        'report_form' : ReportForm()
    }

    return render(request, 'metar_practice/practice.html', data)
