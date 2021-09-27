from django.test import TestCase
import mock
from unittest.mock import patch
from unittest.mock import call

from django.urls import reverse
from django.test.client import Client
from django.conf import settings

from django.forms.models import model_to_dict

import os
import json

from metar_practice.views import practice

from metar_practice.models import Airport
from metar_practice.models import Metar
from metar_practice.models import Answer
from metar_practice.models import Question
from metar_practice.models import Report

from metar_practice.enums import QuestionType

from metar_practice.forms import ReportForm


class TestPracticeView(TestCase):

    def setUp(self):
        db_airport = Airport(name='John F Kennedy International Airport',
                             city='New York',
                             country='United States',
                             icao='KJFK',
                             latitude='40.63980103',
                             longitude='-73.77890015')
        db_airport.full_clean()
        db_airport.save()
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        with open(metar_path) as f:
            metar_json = json.load(f)
        self.db_metar = Metar(metar_json=json.dumps(metar_json),
                              airport=db_airport)
        self.db_metar.full_clean()
        self.db_metar.save()
        self.db_questions = []
        self.questions = []


    def helper_create_db_question(self, db_metar, question_text, answers_text, category):
        db_answers = []
        for answer_text in answers_text:
            db_answer = Answer(text=answer_text)
            db_answer.full_clean()
            db_answer.save()
            db_answers.append(db_answer)
        db_question = Question(metar=db_metar,
                               text=question_text,
                               category=category.value)
        db_question.full_clean()
        db_question.save()
        [db_question.answers.add(db_answer) for db_answer in db_answers]
        return db_question


    def helper_create_db_questions(self, db_metar, questions_answers_text, category):
        db_questions = []
        for question_text, answer_text in questions_answers_text:
            db_answer = Answer(text=answer_text)
            db_answer.full_clean()
            db_answer.save()
            db_question = Question(metar=db_metar,
                                   text=question_text,
                                   category=category.value)
            db_question.full_clean()
            db_question.save()
            db_question.answers.add(db_answer)
            db_questions.append(db_question)
        return db_questions


    def helper_db_question_to_dict(self, db_question):
        question = model_to_dict(db_question)
        answers = []
        for db_answer in question['answers']:
            answers.append(model_to_dict(db_answer))
        question['answers'] = answers
        return question


    def helper_add_db_questions(self, ):
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the airport ICAO?', ['KJFK'], QuestionType.AIRPORT))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is time was this METAR report made?', ['1551 ZULU'], QuestionType.TIME))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the wind direction?', ['350 degrees'], QuestionType.WIND_DIRECTION))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the wind speed?', ['21 kt'], QuestionType.WIND_SPEED))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the wind gusting to?', ['29 kt'], QuestionType.WIND_GUST))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the altimeter?', ['29.66 inHg'], QuestionType.ALTIMETER))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the temperature?', ['10 C'], QuestionType.TEMPERATURE))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the dewpoint?', ['7 C'], QuestionType.DEWPOINT))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the visibility?', ['10 sm'], QuestionType.VISIBILITY))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the reported cloud coverage?', ['Few Clouds', 'Broken Clouds', 'Overcast Clouds'], QuestionType.CLOUD_COVERAGE))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What kind of clouds have a height of 2400 ft?', ['Few'], QuestionType.CLOUD_HEIGHT_INDIVIDUAL))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What kind of clouds have a height of 3600 ft?', ['Scattered'], QuestionType.CLOUD_HEIGHT_INDIVIDUAL))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What kind of clouds have a height of 4600 ft?', ['Overcast'], QuestionType.CLOUD_HEIGHT_INDIVIDUAL))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the height of the few clouds?', ['2400 ft'], QuestionType.CLOUD_HEIGHT_COLLECTIVE))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the height of the broken clouds?', ['3600 ft'], QuestionType.CLOUD_HEIGHT_COLLECTIVE))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the height of the overcast clouds?', ['4600 ft'], QuestionType.CLOUD_HEIGHT_COLLECTIVE))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What are the reported weather codes?', ['Light Rain'], QuestionType.WEATHER_CODES))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What are the reported remarks codes?',
                                                                                ['Automated with precipitation sensor',
                                                                                 'Trace amount of rain in the last hour',
                                                                                 'Rain began at :10'],
                                                                                QuestionType.REMARKS_CODES))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the remarks decimal temperature?', ['10 C'], QuestionType.REMARKS_TEMPERATURE_DECIMAL))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the remarks decimal dewpoint?', ['6.7 C'], QuestionType.REMARKS_DEWPOINT_DECIMAL))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the remarks sea level pressure?', ['1004.2 hPa'], QuestionType.REMARKS_SEA_LEVEL_PRESSURE))
        for db_question in self.db_questions:
            self.questions.append(self.helper_db_question_to_dict(db_question))


    @mock.patch('metar_practice.views.QUESTIONS_TRACEBACK_ALLOWED', 8)
    @mock.patch('metar_practice.models.Question.objects.order_by')
    def test_practice_initial_visit(self, mock_question_order_by):
        self.helper_add_db_questions()
        random_db_question = self.db_questions[0]
        random_question = self.helper_db_question_to_dict(random_db_question)
        mock_question_order_by.side_effect = [Question.objects.filter(pk=random_db_question.pk)]
        response = self.client.get(reverse('practice'))
        self.assertRaises(KeyError)
        session = self.client.session
        self.assertEqual(session['previous_questions'], [random_question])
        self.assertEqual(session['logged'], None)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['airport'], model_to_dict(random_db_question.metar.airport))
        self.assertEquals(response.context['metar'], json.loads(random_db_question.metar.metar_json))
        self.assertEquals(response.context['question'], random_question)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.views.QUESTIONS_TRACEBACK_ALLOWED', 8)
    @mock.patch('metar_practice.models.Question.objects.order_by')
    def test_practice_revisit(self, mock_question_order_by):
        self.helper_add_db_questions()
        random_db_question = self.db_questions[1]
        random_question = self.helper_db_question_to_dict(random_db_question)
        mock_question_order_by.side_effect = [Question.objects.filter(pk=random_db_question.pk)]
        session = self.client.session
        previous_questions = [self.helper_db_question_to_dict(self.db_questions[0])]
        session['previous_questions'] = previous_questions
        session['logged'] = None
        session.save()
        response = self.client.get(reverse('practice'))
        session = self.client.session
        previous_questions.append(random_question)
        self.assertEqual(session['previous_questions'], previous_questions)
        self.assertEqual(session['logged'], None)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['airport'], model_to_dict(random_db_question.metar.airport))
        self.assertEquals(response.context['metar'], json.loads(random_db_question.metar.metar_json))
        self.assertEquals(response.context['question'], random_question)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.views.QUESTIONS_TRACEBACK_ALLOWED', 3)
    @mock.patch('metar_practice.models.Question.objects.order_by')
    def test_practice_overlimit(self, mock_question_order_by):
        QUESTIONS_TRACEBACK_ALLOWED = 3
        self.helper_add_db_questions()
        previous_questions = []
        for i in range(0, QUESTIONS_TRACEBACK_ALLOWED):
            previous_questions.append(self.helper_db_question_to_dict(self.db_questions[i]))
        random_db_question = self.db_questions[QUESTIONS_TRACEBACK_ALLOWED]
        random_question = self.helper_db_question_to_dict(random_db_question)
        mock_question_order_by.side_effect = [Question.objects.filter(pk=random_db_question.pk)]
        session = self.client.session
        session['previous_questions'] = previous_questions
        session['logged'] = None
        session.save()
        response = self.client.get(reverse('practice'))
        session = self.client.session
        previous_questions.append(random_question)
        self.assertEqual(session['previous_questions'], previous_questions[1::])
        self.assertEqual(session['logged'], None)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['airport'], model_to_dict(random_db_question.metar.airport))
        self.assertEquals(response.context['metar'], json.loads(random_db_question.metar.metar_json))
        self.assertEquals(response.context['question'], random_question)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.models.Question.objects.order_by')
    def test_practice_post_form(self, mock_question_order_by):
        self.helper_add_db_questions()
        random_db_question = self.db_questions[1]
        random_question = self.helper_db_question_to_dict(random_db_question)
        form_db_question = self.db_questions[0]
        mock_question_order_by.side_effect = [Question.objects.filter(pk=random_db_question.pk)]
        session = self.client.session
        previous_questions = [self.helper_db_question_to_dict(form_db_question)]
        session['previous_questions'] = previous_questions
        session['logged'] = None
        session.save()
        description = 'The ICAO is incorrectly saying EGLL.'
        form = {'description': description}
        response = self.client.post(reverse('practice'), form, follow=True)
        try:
            db_report = Report.objects.get(description=description,
                                           question=form_db_question)
        except Report.DoesNotExist:
            self.fail()
        self.assertRedirects(response, '/METAR/practice/')
        session = self.client.session
        previous_questions.append(random_question)
        self.assertEqual(session['previous_questions'], previous_questions)
        self.assertEqual(session['logged'], None)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], 'Thank you. Your issue has been logged.')
        self.assertEquals(response.context['airport'], model_to_dict(random_db_question.metar.airport))
        self.assertEquals(response.context['metar'], json.loads(random_db_question.metar.metar_json))
        self.assertEquals(response.context['question'], random_question)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.models.Question.objects.order_by')
    def test_practice_post_form_error_not_valid(self, mock_question_order_by):
        self.helper_add_db_questions()
        random_db_question = self.db_questions[1]
        random_question = self.helper_db_question_to_dict(random_db_question)
        form_db_question = self.db_questions[0]
        mock_question_order_by.side_effect = [Question.objects.filter(pk=random_db_question.pk)]
        session = self.client.session
        previous_questions = [self.helper_db_question_to_dict(form_db_question)]
        session['previous_questions'] = previous_questions
        session['logged'] = None
        session.save()
        description = 'The ICAO is incorrectly saying EGLL.'
        form = {}
        response = self.client.post(reverse('practice'), form, follow=True)
        self.assertEquals(len(Report.objects.all()), 0)
        session = self.client.session
        previous_questions.append(random_question)
        self.assertEqual(session['previous_questions'], previous_questions)
        self.assertEqual(session['logged'], None)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['airport'], model_to_dict(random_db_question.metar.airport))
        self.assertEquals(response.context['metar'], json.loads(random_db_question.metar.metar_json))
        self.assertEquals(response.context['question'], random_question)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.models.Question.objects.order_by')
    def test_practice_post_form_error_question_does_not_exist(self, mock_question_order_by):
        self.helper_add_db_questions()
        random_db_question = self.db_questions[1]
        random_question = self.helper_db_question_to_dict(random_db_question)
        form_db_question = self.db_questions[0]
        mock_question_order_by.side_effect = [Question.objects.filter(pk=random_db_question.pk)]
        session = self.client.session
        previous_questions = [self.helper_db_question_to_dict(form_db_question)]
        session['previous_questions'] = previous_questions
        session['logged'] = None
        session.save()
        description = 'The ICAO is incorrectly saying EGLL.'
        form = {'description': description}
        form_db_question.delete()
        response = self.client.post(reverse('practice'), form, follow=True)
        self.assertRaises(Question.DoesNotExist)
        try:
            db_report = Report.objects.get(description=description)
            self.fail()
        except Report.DoesNotExist:
            pass
        session = self.client.session
        previous_questions.append(random_question)
        self.assertEqual(session['previous_questions'], previous_questions)
        self.assertEqual(session['logged'], None)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['airport'], model_to_dict(random_db_question.metar.airport))
        self.assertEquals(response.context['metar'], json.loads(random_db_question.metar.metar_json))
        self.assertEquals(response.context['question'], random_question)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.models.Question.objects.order_by')
    def test_practice_post_form_error_previous_questions_empty(self, mock_question_order_by):
        self.helper_add_db_questions()
        random_db_question = self.db_questions[0]
        random_question = self.helper_db_question_to_dict(random_db_question)
        mock_question_order_by.side_effect = [Question.objects.filter(pk=random_db_question.pk)]
        description = 'The ICAO is incorrectly saying EGLL.'
        form = {'description': description}
        response = self.client.post(reverse('practice'), form, follow=True)
        self.assertEquals(len(Report.objects.all()), 0)
        session = self.client.session
        self.assertEqual(session['previous_questions'], [random_question])
        self.assertEqual(session['logged'], None)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['airport'], model_to_dict(random_db_question.metar.airport))
        self.assertEquals(response.context['metar'], json.loads(random_db_question.metar.metar_json))
        self.assertEquals(response.context['question'], random_question)
        self.assertEquals(type(response.context['report_form']), ReportForm)

