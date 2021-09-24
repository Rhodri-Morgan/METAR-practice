from django.test import TestCase
import mock
from unittest.mock import call

from django.urls import reverse
from django.test.client import Client
from django.conf import settings

from django.forms.models import model_to_dict

import os
import json
import random
import datetime

from metar_practice.metar_collector import MetarCollector
from metar_practice.question_collector import QuestionColllector

from metar_practice.views import practice
from metar_practice.views import ApiTimeoutError
from metar_practice.views import RanOutOfQuestionsError

from metar_practice.models import Airport
from metar_practice.models import Metar
from metar_practice.models import Answer
from metar_practice.models import Question
from metar_practice.models import Report

from metar_practice.forms import ReportForm


class TestPracticeView(TestCase):

    def helper_create_airport_object(self, name, city, country, icao, latitude, longitude):
        db_airport = Airport(name=name,
                             city=city,
                             country=country,
                             icao=icao,
                             latitude=latitude,
                             longitude=longitude)
        db_airport.full_clean()
        db_airport.save()
        return db_airport


    def helper_create_metar_object(self, path, db_airport):
        metar_json = None
        with open(path) as f:
            metar_json = json.load(f)
        db_metar = Metar(metar_json=json.dumps(metar_json),
                         airport=db_airport)
        db_metar.full_clean()
        db_metar.save()
        return json.loads(db_metar.metar_json), db_metar


    def helper_create_db_question(self, db_metar, question_text, answers_text):
        db_answers = []
        for answer_text in answers_text:
            db_answer = Answer(text=answer_text)
            db_answer.full_clean()
            db_answer.save()
            db_answers.append(db_answer)
        db_question = Question(metar=db_metar,
                               text=question_text)
        db_question.full_clean()
        db_question.save()
        [db_question.answers.add(db_answer) for db_answer in db_answers]
        return db_question


    def setUp(self):
        self.API_TIMEOUT_THRESHOLD = 5                   # None will reflect no limit
        self.QUESTION_SAMPLE_COUNT = 5
        self.db_questions = []
        self.db_airport = self.helper_create_airport_object('John F Kennedy International Airport',
                                                            'New York',
                                                            'United States',
                                                            'KJFK',
                                                            '40.63980103',
                                                            '-73.77890015')
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'views', 'sample_metar_KJFK.json')
        self.metar_json, self.db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the airport ICAO?', ['KJFK']))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is time was this METAR report made?', ['1551 ZULU']))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the wind direction?', ['350 degrees']))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the wind speed?', ['21 kt']))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the wind gusting to?', ['29 kt']))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the altimeter?', ['29.66 inHg']))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the temperature?', ['10 C']))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the dewpoint?', ['7 C']))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the visibility?', ['10 sm']))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the reported cloud coverage?', ['Few Clouds', 'Broken Clouds', 'Overcast Clouds']))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the height of the few clouds?', ['2400 ft']))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the height of the broken clouds?', ['3600 ft']))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What is the height of the overcast clouds?', ['4600 ft']))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What kind of clouds have a ceiling of 2400 ft?', ['Few']))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What kind of clouds have a ceiling of 3600 ft?', ['Scattered']))
        self.db_questions.append(self.helper_create_db_question(self.db_metar, 'What kind of clouds have a ceiling of 4600 ft?', ['Overcast']))


    def helper_question_to_dict(self, db_question):
        question = model_to_dict(db_question)
        answers = []
        for db_answer in question['answers']:
            answers.append(model_to_dict(db_answer))
        question['answers'] = answers
        return question


    def helper_get_questions(self, count):
        db_questions = []
        for db_question in self.questions.values():
            db_questions.append(db_question)
        return db_questions


    @mock.patch('metar_practice.views.QuestionColllector')
    @mock.patch('metar_practice.views.MetarCollector')
    def test_practice_initial_visit(self, mock_metar_collector, mock_question_collector):
        instance_mock_metar_collector = mock_metar_collector.return_value
        instance_mock_question_collector = mock_question_collector.return_value
        instance_mock_metar_collector.get_random_airport.return_value = self.db_airport
        instance_mock_metar_collector.get_raw_metar.return_value = (200, self.db_metar)
        instance_mock_question_collector.generate_questions.return_value = self.db_questions[:self.QUESTION_SAMPLE_COUNT]
        response = self.client.get(reverse('practice'))
        self.assertRaises(KeyError)
        session = self.client.session
        instance_mock_metar_collector.get_random_airport.assert_called_once()
        instance_mock_metar_collector.get_raw_metar.assert_called_once()
        instance_mock_question_collector.generate_questions.assert_called_once()
        self.assertEqual(session['status'], 200)
        self.assertEqual(session['airport'], model_to_dict(self.db_airport))
        self.assertEqual(session['metar'], self.metar_json)
        self.assertEqual(session['questions'], [self.helper_question_to_dict(db_question) for db_question in self.db_questions][1:self.QUESTION_SAMPLE_COUNT:])
        self.assertEqual(session['api'], {'timeout' : False, 'end_timeout' : None})
        self.assertEqual(session['previous_question'], self.helper_question_to_dict(self.db_questions[0]))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['status'], 200)
        self.assertEquals(response.context['airport'], model_to_dict(self.db_airport))
        self.assertEquals(response.context['metar'], self.metar_json)
        self.assertEquals(response.context['question'], self.helper_question_to_dict(self.db_questions[0]))
        self.assertEquals(response.context['refresh_needed'], False)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.views.QuestionColllector')
    @mock.patch('metar_practice.views.MetarCollector')
    def test_practice_revisit(self, mock_metar_collector, mock_question_collector):
        instance_mock_metar_collector = mock_metar_collector.return_value
        instance_mock_question_collector = mock_question_collector.return_value
        instance_mock_metar_collector.get_random_airport.return_value = self.db_airport
        instance_mock_metar_collector.get_raw_metar.return_value = (200, self.db_metar)
        instance_mock_question_collector.generate_questions.return_value = self.db_questions[:self.QUESTION_SAMPLE_COUNT]
        session = self.client.session
        session['status'] = 200
        session['airport'] = model_to_dict(self.db_airport)
        session['metar'] = self.metar_json
        session['questions'] = [self.helper_question_to_dict(db_question) for db_question in self.db_questions][1:self.QUESTION_SAMPLE_COUNT:]
        session['api'] = {'timeout' : False, 'end_timeout' : None}
        session['previous_question'] = self.helper_question_to_dict(self.db_questions[0])
        session.save()
        response = self.client.get(reverse('practice'))
        session = self.client.session
        instance_mock_metar_collector.get_random_airport.assert_not_called()
        instance_mock_metar_collector.get_raw_metar.assert_not_called()
        instance_mock_question_collector.generate_questions.assert_not_called()
        self.assertEqual(session['status'], 200)
        self.assertEqual(session['airport'], model_to_dict(self.db_airport))
        self.assertEqual(session['metar'], self.metar_json)
        self.assertEqual(session['questions'], [self.helper_question_to_dict(db_question) for db_question in self.db_questions][2:self.QUESTION_SAMPLE_COUNT:])
        self.assertEqual(session['api'], {'timeout' : False, 'end_timeout' : None})
        self.assertEqual(session['previous_question'], self.helper_question_to_dict(self.db_questions[1]))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['status'], 200)
        self.assertEquals(response.context['airport'], model_to_dict(self.db_airport))
        self.assertEquals(response.context['metar'], self.metar_json)
        self.assertEquals(response.context['question'], self.helper_question_to_dict(self.db_questions[1]))
        self.assertEquals(response.context['refresh_needed'], False)
        self.assertEquals(type(response.context['report_form']), ReportForm)



    @mock.patch('metar_practice.views.QuestionColllector')
    @mock.patch('metar_practice.views.MetarCollector')
    def test_practice_final_question(self, mock_metar_collector, mock_question_collector):
        instance_mock_metar_collector = mock_metar_collector.return_value
        instance_mock_question_collector = mock_question_collector.return_value
        instance_mock_metar_collector.get_random_airport.return_value = self.db_airport
        instance_mock_metar_collector.get_raw_metar.return_value = (200, self.db_metar)
        instance_mock_question_collector.generate_questions.return_value = self.db_questions[:self.QUESTION_SAMPLE_COUNT]
        session = self.client.session
        session['status'] = 200
        session['airport'] = model_to_dict(self.db_airport)
        session['metar'] = self.metar_json
        session['questions'] = [self.helper_question_to_dict(db_question) for db_question in self.db_questions][self.QUESTION_SAMPLE_COUNT-1:self.QUESTION_SAMPLE_COUNT:]
        session['api'] = {'timeout' : False, 'end_timeout' : None}
        session['previous_question'] = self.helper_question_to_dict(self.db_questions[self.QUESTION_SAMPLE_COUNT-2])
        session.save()
        response = self.client.get(reverse('practice'))
        session = self.client.session
        instance_mock_metar_collector.get_random_airport.assert_not_called()
        instance_mock_metar_collector.get_raw_metar.assert_not_called()
        instance_mock_question_collector.generate_questions.assert_not_called()
        self.assertEqual(session['status'], 200)
        self.assertEqual(session['airport'], model_to_dict(self.db_airport))
        self.assertEqual(session['metar'], self.metar_json)
        self.assertEqual(session['questions'], [])
        self.assertEqual(session['api'], {'timeout' : False, 'end_timeout' : None})
        self.assertEqual(session['previous_question'], self.helper_question_to_dict(self.db_questions[self.QUESTION_SAMPLE_COUNT-1]))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['status'], 200)
        self.assertEquals(response.context['airport'], model_to_dict(self.db_airport))
        self.assertEquals(response.context['metar'], self.metar_json)
        self.assertEquals(response.context['question'], self.helper_question_to_dict(self.db_questions[self.QUESTION_SAMPLE_COUNT-1]))
        self.assertEquals(response.context['refresh_needed'], True)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.views.QuestionColllector')
    @mock.patch('metar_practice.views.MetarCollector')
    def test_practice_refresh_questions(self, mock_metar_collector, mock_question_collector):
        db_airport_replacement = self.helper_create_airport_object('London Heathrow Airport',
                                                                   'London',
                                                                   'United Kingdom',
                                                                   'EGLL',
                                                                   '51.4706',
                                                                   '-0.461941')
        metar_path_replacement = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'views', 'sample_metar_EGLL.json')
        metar_json_replacement, db_metar_replacement = self.helper_create_metar_object(metar_path_replacement, db_airport_replacement)
        instance_mock_metar_collector = mock_metar_collector.return_value
        instance_mock_question_collector = mock_question_collector.return_value
        instance_mock_metar_collector.get_random_airport.return_value = db_airport_replacement
        instance_mock_metar_collector.get_raw_metar.return_value = (200, db_metar_replacement)
        db_questions_replacement = []
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the airport ICAO?', ['EGLL']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is time was this METAR report made?', ['1250 ZULU']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the wind direction?', ['250 degrees']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the wind speed?', ['13 kt']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the wind gusting to?', ['The wind is not currently gusting.']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the altimeter?', ['1019 hPa']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the temperature?', ['20 C']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the dewpoint?', ['15 C']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the visibility?', ['9999 sm']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the reported cloud coverage?', ['Scattered Clouds', 'Broken Clouds', 'Overcast Clouds']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the height of the Scattered clouds?', ['2300 ft']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the height of the broken clouds?', ['2700 ft']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the height of the overcast clouds?', ['3100 ft']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What kind of clouds have a ceiling of 2300 ft?', ['Scattered']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What kind of clouds have a ceiling of 2700 ft?', ['Broken']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What kind of clouds have a ceiling of 4600 ft?', ['Overcast']))
        instance_mock_question_collector.generate_questions.return_value = db_questions_replacement[:self.QUESTION_SAMPLE_COUNT]
        session = self.client.session
        session['status'] = 200
        session['airport'] = model_to_dict(self.db_airport)
        session['metar'] = self.metar_json
        session['questions'] = []
        session['api'] = {'timeout' : False, 'end_timeout' : None}
        session['previous_question'] = self.helper_question_to_dict(self.db_questions[self.QUESTION_SAMPLE_COUNT-1])
        session.save()
        response = self.client.get(reverse('practice'))
        self.assertRaises(RanOutOfQuestionsError)
        session = self.client.session
        instance_mock_metar_collector.get_random_airport.assert_called_once()
        instance_mock_metar_collector.get_raw_metar.assert_called_once()
        instance_mock_question_collector.generate_questions.assert_called_once()
        self.assertEqual(session['status'], 200)
        self.assertEqual(session['airport'], model_to_dict(db_airport_replacement))
        self.assertEqual(session['metar'], metar_json_replacement)
        self.assertEqual(session['questions'], [self.helper_question_to_dict(db_question) for db_question in db_questions_replacement][1:self.QUESTION_SAMPLE_COUNT:])
        self.assertEqual(session['api'], {'timeout' : False, 'end_timeout' : None})
        self.assertEqual(session['previous_question'], self.helper_question_to_dict(db_questions_replacement[0]))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['status'], 200)
        self.assertEquals(response.context['airport'], model_to_dict(db_airport_replacement))
        self.assertEquals(response.context['metar'], metar_json_replacement)
        self.assertEquals(response.context['question'], self.helper_question_to_dict(db_questions_replacement[0]))
        self.assertEquals(response.context['refresh_needed'], False)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.views.QuestionColllector')
    @mock.patch('metar_practice.views.MetarCollector')
    def test_practice_airport_none(self, mock_metar_collector, mock_question_collector):
        instance_mock_metar_collector = mock_metar_collector.return_value
        instance_mock_question_collector = mock_question_collector.return_value
        instance_mock_metar_collector.get_random_airport.side_effect = [None, self.db_airport]
        instance_mock_metar_collector.get_raw_metar.return_value = (200, self.db_metar)
        instance_mock_question_collector.generate_questions.return_value = self.db_questions[:self.QUESTION_SAMPLE_COUNT]
        response = self.client.get(reverse('practice'))
        self.assertRaises(KeyError)
        session = self.client.session
        self.assertEqual(instance_mock_metar_collector.get_random_airport.call_count, 2)
        instance_mock_metar_collector.get_raw_metar.assert_called_once()
        instance_mock_question_collector.generate_questions.assert_called_once()
        self.assertEqual(session['status'], 200)
        self.assertEqual(session['airport'], model_to_dict(self.db_airport))
        self.assertEqual(session['metar'], self.metar_json)
        self.assertEqual(session['questions'], [self.helper_question_to_dict(db_question) for db_question in self.db_questions][1:self.QUESTION_SAMPLE_COUNT:])
        self.assertEqual(session['api'], {'timeout' : False, 'end_timeout' : None})
        self.assertEqual(session['previous_question'], self.helper_question_to_dict(self.db_questions[0]))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['status'], 200)
        self.assertEquals(response.context['airport'], model_to_dict(self.db_airport))
        self.assertEquals(response.context['metar'], self.metar_json)
        self.assertEquals(response.context['question'], self.helper_question_to_dict(self.db_questions[0]))
        self.assertEquals(response.context['refresh_needed'], False)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.views.QuestionColllector')
    @mock.patch('metar_practice.views.MetarCollector')
    def test_practice_status_none_metar_none(self, mock_metar_collector, mock_question_collector):
        instance_mock_metar_collector = mock_metar_collector.return_value
        instance_mock_question_collector = mock_question_collector.return_value
        instance_mock_metar_collector.get_random_airport.return_value = self.db_airport
        instance_mock_metar_collector.get_raw_metar.side_effect = [(None, None), (200, self.db_metar)]
        instance_mock_question_collector.generate_questions.return_value = self.db_questions[:self.QUESTION_SAMPLE_COUNT]
        response = self.client.get(reverse('practice'))
        self.assertRaises(KeyError)
        session = self.client.session
        self.assertEqual(instance_mock_metar_collector.get_random_airport.call_count, 2)
        self.assertEqual(instance_mock_metar_collector.get_raw_metar.call_count, 2)
        instance_mock_question_collector.generate_questions.assert_called_once()
        self.assertEqual(session['status'], 200)
        self.assertEqual(session['airport'], model_to_dict(self.db_airport))
        self.assertEqual(session['metar'], self.metar_json)
        self.assertEqual(session['questions'], [self.helper_question_to_dict(db_question) for db_question in self.db_questions][1:self.QUESTION_SAMPLE_COUNT:])
        self.assertEqual(session['api'], {'timeout' : False, 'end_timeout' : None})
        self.assertEqual(session['previous_question'], self.helper_question_to_dict(self.db_questions[0]))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['status'], 200)
        self.assertEquals(response.context['airport'], model_to_dict(self.db_airport))
        self.assertEquals(response.context['metar'], self.metar_json)
        self.assertEquals(response.context['question'], self.helper_question_to_dict(self.db_questions[0]))
        self.assertEquals(response.context['refresh_needed'], False)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.views.QuestionColllector')
    @mock.patch('metar_practice.views.MetarCollector')
    def test_practice_status_400_metar_none(self, mock_metar_collector, mock_question_collector):
        instance_mock_metar_collector = mock_metar_collector.return_value
        instance_mock_question_collector = mock_question_collector.return_value
        instance_mock_metar_collector.get_random_airport.return_value = self.db_airport
        instance_mock_metar_collector.get_raw_metar.side_effect = [(400, None), (200, self.db_metar)]
        instance_mock_question_collector.generate_questions.return_value = self.db_questions[:self.QUESTION_SAMPLE_COUNT]
        response = self.client.get(reverse('practice'))
        self.assertRaises(KeyError)
        session = self.client.session
        self.assertEqual(instance_mock_metar_collector.get_random_airport.call_count, 2)
        self.assertEqual(instance_mock_metar_collector.get_raw_metar.call_count, 2)
        instance_mock_question_collector.generate_questions.assert_called_once()
        self.assertEqual(session['status'], 200)
        self.assertEqual(session['airport'], model_to_dict(self.db_airport))
        self.assertEqual(session['metar'], self.metar_json)
        self.assertEqual(session['questions'], [self.helper_question_to_dict(db_question) for db_question in self.db_questions][1:self.QUESTION_SAMPLE_COUNT:])
        self.assertEqual(session['api'], {'timeout' : False, 'end_timeout' : None})
        self.assertEqual(session['previous_question'], self.helper_question_to_dict(self.db_questions[0]))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['status'], 200)
        self.assertEquals(response.context['airport'], model_to_dict(self.db_airport))
        self.assertEquals(response.context['metar'], self.metar_json)
        self.assertEquals(response.context['question'], self.helper_question_to_dict(self.db_questions[0]))
        self.assertEquals(response.context['refresh_needed'], False)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.views.QuestionColllector')
    @mock.patch('metar_practice.views.MetarCollector')
    def test_practice_status_questions_none(self, mock_metar_collector, mock_question_collector):
        instance_mock_metar_collector = mock_metar_collector.return_value
        instance_mock_question_collector = mock_question_collector.return_value
        instance_mock_metar_collector.get_random_airport.return_value = self.db_airport
        instance_mock_metar_collector.get_raw_metar.return_value = (200, self.db_metar)
        instance_mock_question_collector.generate_questions.side_effect = [None, self.db_questions[:self.QUESTION_SAMPLE_COUNT]]
        response = self.client.get(reverse('practice'))
        self.assertRaises(KeyError)
        session = self.client.session
        self.assertEqual(instance_mock_metar_collector.get_random_airport.call_count, 2)
        self.assertEqual(instance_mock_metar_collector.get_raw_metar.call_count, 2)
        self.assertEqual(instance_mock_question_collector.generate_questions.call_count, 2)
        self.assertEqual(session['status'], 200)
        self.assertEqual(session['airport'], model_to_dict(self.db_airport))
        self.assertEqual(session['metar'], self.metar_json)
        self.assertEqual(session['questions'], [self.helper_question_to_dict(db_question) for db_question in self.db_questions][1:self.QUESTION_SAMPLE_COUNT:])
        self.assertEqual(session['api'], {'timeout' : False, 'end_timeout' : None})
        self.assertEqual(session['previous_question'], self.helper_question_to_dict(self.db_questions[0]))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['status'], 200)
        self.assertEquals(response.context['airport'], model_to_dict(self.db_airport))
        self.assertEquals(response.context['metar'], self.metar_json)
        self.assertEquals(response.context['question'], self.helper_question_to_dict(self.db_questions[0]))
        self.assertEquals(response.context['refresh_needed'], False)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.views.QuestionColllector')
    @mock.patch('metar_practice.views.MetarCollector')
    def test_practice_begin_timeout(self, mock_metar_collector, mock_question_collector):
        instance_mock_metar_collector = mock_metar_collector.return_value
        instance_mock_question_collector = mock_question_collector.return_value
        instance_mock_metar_collector.get_random_airport.return_value = self.db_airport
        instance_mock_metar_collector.get_raw_metar.return_value = (None, None)
        instance_mock_question_collector.generate_questions.return_value = None
        response = self.client.get(reverse('practice'))
        self.assertRaises(KeyError)
        self.assertRaises(ApiTimeoutError)
        session = self.client.session
        self.assertEqual(instance_mock_metar_collector.get_random_airport.call_count, self.API_TIMEOUT_THRESHOLD)
        self.assertEqual(instance_mock_metar_collector.get_raw_metar.call_count, self.API_TIMEOUT_THRESHOLD)
        instance_mock_question_collector.generate_questions.assert_not_called()
        self.assertEqual(session['status'], 400)
        self.assertEqual(session['airport'], model_to_dict(self.db_airport))
        self.assertEqual(session['metar'], self.metar_json)
        self.assertEqual(len(session['questions']), self.QUESTION_SAMPLE_COUNT-1)
        db_questions_dict = [self.helper_question_to_dict(db_question) for db_question in self.db_questions]
        [self.assertTrue(returned_question in db_questions_dict) for returned_question in session['questions']]
        self.assertEqual(session['api']['timeout'], True)
        self.assertEqual(session['api']['end_timeout'][:-3:], (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).strftime('%m/%d/%Y, %H:%M'))
        previous_question = None
        for question_dict in db_questions_dict:
            if session['previous_question'] == question_dict and question_dict not in session['questions']:
                previous_question = question_dict
                break
        self.assertIsNotNone(previous_question)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['status'], 400)
        self.assertEquals(response.context['airport'], model_to_dict(self.db_airport))
        self.assertEquals(response.context['metar'], self.metar_json)
        self.assertEquals(response.context['question'], previous_question)
        self.assertEquals(response.context['refresh_needed'], False)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.views.QuestionColllector')
    @mock.patch('metar_practice.views.MetarCollector')
    def test_practice_continue_timeout(self, mock_metar_collector, mock_question_collector):
        instance_mock_metar_collector = mock_metar_collector.return_value
        instance_mock_question_collector = mock_question_collector.return_value
        instance_mock_metar_collector.get_random_airport.return_value = None
        instance_mock_metar_collector.get_raw_metar.return_value = (None, None)
        instance_mock_question_collector.generate_questions.return_value = None
        session = self.client.session
        session['status'] = 400
        session['airport'] = model_to_dict(self.db_airport)
        session['metar'] = self.metar_json
        session['questions'] = [self.helper_question_to_dict(db_question) for db_question in self.db_questions][1:self.QUESTION_SAMPLE_COUNT:]
        end_timeout = (datetime.datetime.utcnow() + datetime.timedelta(minutes=30)).strftime('%m/%d/%Y, %H:%M:%S')
        session['api'] = {'timeout' : True, 'end_timeout' : end_timeout}
        session['previous_question'] = self.helper_question_to_dict(self.db_questions[0])
        session.save()
        response = self.client.get(reverse('practice'))
        self.assertRaises(ApiTimeoutError)
        session = self.client.session
        instance_mock_metar_collector.get_random_airport.assert_not_called()
        instance_mock_metar_collector.get_raw_metar.assert_not_called()
        instance_mock_question_collector.generate_questions.assert_not_called()
        self.assertEqual(session['status'], 400)
        self.assertEqual(session['airport'], model_to_dict(self.db_airport))
        self.assertEqual(session['metar'], self.metar_json)
        self.assertEqual(session['questions'], [self.helper_question_to_dict(db_question) for db_question in self.db_questions][2:self.QUESTION_SAMPLE_COUNT:])
        self.assertEqual(session['api'], {'timeout' : True, 'end_timeout' : end_timeout})
        self.assertEqual(session['previous_question'], self.helper_question_to_dict(self.db_questions[1]))
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['status'], 400)
        self.assertEquals(response.context['airport'], model_to_dict(self.db_airport))
        self.assertEquals(response.context['metar'], self.metar_json)
        self.assertEquals(response.context['question'], self.helper_question_to_dict(self.db_questions[1]))
        self.assertEquals(response.context['refresh_needed'], False)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.views.QuestionColllector')
    @mock.patch('metar_practice.views.MetarCollector')
    def test_practice_timeout_questions_equal_sample_count(self, mock_metar_collector, mock_question_collector):
        instance_mock_metar_collector = mock_metar_collector.return_value
        instance_mock_question_collector = mock_question_collector.return_value
        instance_mock_metar_collector.get_random_airport.return_value = self.db_airport
        instance_mock_metar_collector.get_raw_metar.return_value = (None, None)
        instance_mock_question_collector.generate_questions.return_value = None
        db_questions_replacement = []
        for i in range(0, self.QUESTION_SAMPLE_COUNT):
            db_questions_replacement.append(self.db_questions[i])
        for db_question in self.db_questions:
            if db_question not in db_questions_replacement:
                db_question.delete()
        response = self.client.get(reverse('practice'))
        self.assertRaises(KeyError)
        self.assertRaises(ApiTimeoutError)
        session = self.client.session
        self.assertEqual(instance_mock_metar_collector.get_random_airport.call_count, self.API_TIMEOUT_THRESHOLD)
        self.assertEqual(instance_mock_metar_collector.get_raw_metar.call_count, self.API_TIMEOUT_THRESHOLD)
        instance_mock_question_collector.generate_questions.assert_not_called()
        self.assertEqual(session['status'], 400)
        self.assertEqual(session['airport'], model_to_dict(self.db_airport))
        self.assertEqual(session['metar'], self.metar_json)
        self.assertEqual(len(session['questions']), len(db_questions_replacement)-1)
        db_questions_replacement_dict = [self.helper_question_to_dict(db_question) for db_question in db_questions_replacement]
        [self.assertTrue(returned_question in db_questions_replacement_dict) for returned_question in session['questions']]
        self.assertEqual(session['api']['timeout'], True)
        self.assertEqual(session['api']['end_timeout'][:-3:], (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).strftime('%m/%d/%Y, %H:%M'))
        previous_question = None
        for question_dict in db_questions_replacement_dict:
            if session['previous_question'] == question_dict and question_dict not in session['questions']:
                previous_question = question_dict
                break
        self.assertIsNotNone(previous_question)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['status'], 400)
        self.assertEquals(response.context['airport'], model_to_dict(self.db_airport))
        self.assertEquals(response.context['metar'], self.metar_json)
        self.assertEquals(response.context['question'], previous_question)
        self.assertEquals(response.context['refresh_needed'], False)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.views.QuestionColllector')
    @mock.patch('metar_practice.views.MetarCollector')
    def test_practice_timeout_questions_below_sample_count(self, mock_metar_collector, mock_question_collector):
        instance_mock_metar_collector = mock_metar_collector.return_value
        instance_mock_question_collector = mock_question_collector.return_value
        instance_mock_metar_collector.get_random_airport.return_value = self.db_airport
        instance_mock_metar_collector.get_raw_metar.return_value = (None, None)
        instance_mock_question_collector.generate_questions.return_value = None
        db_questions_replacement = []
        for i in range(0, self.QUESTION_SAMPLE_COUNT-1):
            db_questions_replacement.append(self.db_questions[i])
        for db_question in self.db_questions:
            if db_question not in db_questions_replacement:
                db_question.delete()
        response = self.client.get(reverse('practice'))
        self.assertRaises(KeyError)
        self.assertRaises(ApiTimeoutError)
        session = self.client.session
        self.assertEqual(instance_mock_metar_collector.get_random_airport.call_count, self.API_TIMEOUT_THRESHOLD)
        self.assertEqual(instance_mock_metar_collector.get_raw_metar.call_count, self.API_TIMEOUT_THRESHOLD)
        instance_mock_question_collector.generate_questions.assert_not_called()
        self.assertEqual(session['status'], 400)
        self.assertEqual(session['airport'], model_to_dict(self.db_airport))
        self.assertEqual(session['metar'], self.metar_json)
        self.assertEqual(len(session['questions']), len(db_questions_replacement)-1)
        db_questions_replacement_dict = [self.helper_question_to_dict(db_question) for db_question in db_questions_replacement]
        [self.assertTrue(returned_question in db_questions_replacement_dict) for returned_question in session['questions']]
        self.assertEqual(session['api']['timeout'], True)
        self.assertEqual(session['api']['end_timeout'][:-3:], (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).strftime('%m/%d/%Y, %H:%M'))
        previous_question = None
        for question_dict in db_questions_replacement_dict:
            if session['previous_question'] == question_dict and question_dict not in session['questions']:
                previous_question = question_dict
                break
        self.assertIsNotNone(previous_question)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['status'], 400)
        self.assertEquals(response.context['airport'], model_to_dict(self.db_airport))
        self.assertEquals(response.context['metar'], self.metar_json)
        self.assertEquals(response.context['question'], previous_question)
        self.assertEquals(response.context['refresh_needed'], False)
        self.assertEquals(type(response.context['report_form']), ReportForm)



    @mock.patch('metar_practice.models.Metar.objects.order_by')
    @mock.patch('metar_practice.views.QuestionColllector')
    @mock.patch('metar_practice.views.MetarCollector')
    def test_practice_timeout_zero_questions(self, mock_metar_collector, mock_question_collector, mock_metar_objects_order_by):
        Question.objects.all().delete()
        db_airport_replacement = self.helper_create_airport_object('London Heathrow Airport',
                                                                   'London',
                                                                   'United Kingdom',
                                                                   'EGLL',
                                                                   '51.4706',
                                                                   '-0.461941')
        metar_path_replacement = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'views', 'sample_metar_EGLL.json')
        metar_json_replacement, db_metar_replacement = self.helper_create_metar_object(metar_path_replacement, db_airport_replacement)
        db_questions_replacement = []
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the airport ICAO?', ['EGLL']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is time was this METAR report made?', ['1250 ZULU']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the wind direction?', ['250 degrees']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the wind speed?', ['13 kt']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the wind gusting to?', ['The wind is not currently gusting.']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the altimeter?', ['1019 hPa']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the temperature?', ['20 C']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the dewpoint?', ['15 C']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the visibility?', ['9999 sm']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the reported cloud coverage?', ['Scattered Clouds', 'Broken Clouds', 'Overcast Clouds']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the height of the Scattered clouds?', ['2300 ft']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the height of the broken clouds?', ['2700 ft']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What is the height of the overcast clouds?', ['3100 ft']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What kind of clouds have a ceiling of 2300 ft?', ['Scattered']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What kind of clouds have a ceiling of 2700 ft?', ['Broken']))
        db_questions_replacement.append(self.helper_create_db_question(db_metar_replacement, 'What kind of clouds have a ceiling of 4600 ft?', ['Overcast']))
        mock_metar_objects_order_by.side_effect = [Metar.objects.filter(pk=self.db_metar.pk), Metar.objects.filter(pk=db_metar_replacement.pk)]
        instance_mock_metar_collector = mock_metar_collector.return_value
        instance_mock_question_collector = mock_question_collector.return_value
        instance_mock_metar_collector.get_random_airport.return_value = self.db_airport
        instance_mock_metar_collector.get_raw_metar.return_value = (None, None)
        instance_mock_question_collector.generate_questions.return_value = None
        response = self.client.get(reverse('practice'))
        self.assertRaises(KeyError)
        self.assertRaises(ApiTimeoutError)
        session = self.client.session
        self.assertEqual(instance_mock_metar_collector.get_random_airport.call_count, self.API_TIMEOUT_THRESHOLD)
        self.assertEqual(instance_mock_metar_collector.get_raw_metar.call_count, self.API_TIMEOUT_THRESHOLD)
        instance_mock_question_collector.generate_questions.assert_not_called()
        self.assertEqual(session['status'], 400)
        self.assertEqual(session['airport'], model_to_dict(db_airport_replacement))
        self.assertEqual(session['metar'], metar_json_replacement)
        self.assertEqual(len(session['questions']), self.QUESTION_SAMPLE_COUNT-1)
        db_questions_dict = [self.helper_question_to_dict(db_question) for db_question in db_questions_replacement]
        [self.assertTrue(returned_question in db_questions_dict) for returned_question in session['questions']]
        self.assertEqual(session['api']['timeout'], True)
        self.assertEqual(session['api']['end_timeout'][:-3:], (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).strftime('%m/%d/%Y, %H:%M'))
        previous_question = None
        for question_dict in db_questions_dict:
            if session['previous_question'] == question_dict and question_dict not in session['questions']:
                previous_question = question_dict
                break
        self.assertIsNotNone(previous_question)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['status'], 400)
        self.assertEquals(response.context['airport'], model_to_dict(db_airport_replacement))
        self.assertEquals(response.context['metar'], metar_json_replacement)
        self.assertEquals(response.context['question'], previous_question)
        self.assertEquals(response.context['refresh_needed'], False)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.views.QuestionColllector')
    @mock.patch('metar_practice.views.MetarCollector')
    def test_practice_post_form(self, mock_metar_collector, mock_question_collector):
        instance_mock_metar_collector = mock_metar_collector.return_value
        instance_mock_question_collector = mock_question_collector.return_value
        instance_mock_metar_collector.get_random_airport.return_value = self.db_airport
        instance_mock_metar_collector.get_raw_metar.return_value = (200, self.db_metar)
        instance_mock_question_collector.generate_questions.return_value = self.db_questions[:self.QUESTION_SAMPLE_COUNT]
        session = self.client.session
        session['status'] = 200
        session['airport'] = model_to_dict(self.db_airport)
        session['metar'] = self.metar_json
        session['questions'] = [self.helper_question_to_dict(db_question) for db_question in self.db_questions][1:self.QUESTION_SAMPLE_COUNT:]
        session['api'] = {'timeout' : False, 'end_timeout' : None}
        session['previous_question'] = self.helper_question_to_dict(self.db_questions[0])
        session.save()
        description = 'The ICAO is incorrectly saying EGLL.'
        form = {'description': description}
        response = self.client.post(reverse('practice'), form, follow=True)
        try:
            db_report = Report.objects.get(description=description,
                                           question=self.db_questions[0])
        except Report.DoesNotExist:
            self.fail()
        self.assertRedirects(response, '/METAR/practice/')
        session = self.client.session
        instance_mock_metar_collector.get_random_airport.assert_not_called()
        instance_mock_metar_collector.get_raw_metar.assert_not_called()
        instance_mock_question_collector.generate_questions.assert_not_called()
        self.assertEqual(session['status'], 200)
        self.assertEqual(session['airport'], model_to_dict(self.db_airport))
        self.assertEqual(session['metar'], self.metar_json)
        self.assertEqual(session['questions'], [self.helper_question_to_dict(db_question) for db_question in self.db_questions][2:self.QUESTION_SAMPLE_COUNT:])
        self.assertEqual(session['api'], {'timeout' : False, 'end_timeout' : None})
        self.assertEqual(session['previous_question'], self.helper_question_to_dict(self.db_questions[1]))
        self.assertEqual(session['logged'], None)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], 'Thank you. Your issue has been logged.')
        self.assertEquals(response.context['status'], 200)
        self.assertEquals(response.context['airport'], model_to_dict(self.db_airport))
        self.assertEquals(response.context['metar'], self.metar_json)
        self.assertEquals(response.context['question'], self.helper_question_to_dict(self.db_questions[1]))
        self.assertEquals(response.context['refresh_needed'], False)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.views.QuestionColllector')
    @mock.patch('metar_practice.views.MetarCollector')
    def test_practice_post_form_error_not_valid(self, mock_metar_collector, mock_question_collector):
        instance_mock_metar_collector = mock_metar_collector.return_value
        instance_mock_question_collector = mock_question_collector.return_value
        instance_mock_metar_collector.get_random_airport.return_value = self.db_airport
        instance_mock_metar_collector.get_raw_metar.return_value = (200, self.db_metar)
        instance_mock_question_collector.generate_questions.return_value = self.db_questions[:self.QUESTION_SAMPLE_COUNT]
        session = self.client.session
        session['status'] = 200
        session['airport'] = model_to_dict(self.db_airport)
        session['metar'] = self.metar_json
        session['questions'] = [self.helper_question_to_dict(db_question) for db_question in self.db_questions][1:self.QUESTION_SAMPLE_COUNT:]
        session['api'] = {'timeout' : False, 'end_timeout' : None}
        session['previous_question'] = self.helper_question_to_dict(self.db_questions[0])
        session.save()
        description = 'The ICAO is incorrectly saying EGLL.'
        form = {}
        response = self.client.post(reverse('practice'), form, follow=True)
        try:
            db_report = Report.objects.get(question=self.db_questions[0])
            self.fail()
        except Report.DoesNotExist:
            pass
        session = self.client.session
        instance_mock_metar_collector.get_random_airport.assert_not_called()
        instance_mock_metar_collector.get_raw_metar.assert_not_called()
        instance_mock_question_collector.generate_questions.assert_not_called()
        self.assertEqual(session['status'], 200)
        self.assertEqual(session['airport'], model_to_dict(self.db_airport))
        self.assertEqual(session['metar'], self.metar_json)
        self.assertEqual(session['questions'], [self.helper_question_to_dict(db_question) for db_question in self.db_questions][2:self.QUESTION_SAMPLE_COUNT:])
        self.assertEqual(session['api'], {'timeout' : False, 'end_timeout' : None})
        self.assertEqual(session['previous_question'], self.helper_question_to_dict(self.db_questions[1]))
        try:
            self.assertEqual(session['logged'], 'Thank you. Your issue has been logged.')
            self.fail()
        except KeyError:
            pass
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['status'], 200)
        self.assertEquals(response.context['airport'], model_to_dict(self.db_airport))
        self.assertEquals(response.context['metar'], self.metar_json)
        self.assertEquals(response.context['question'], self.helper_question_to_dict(self.db_questions[1]))
        self.assertEquals(response.context['refresh_needed'], False)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.views.QuestionColllector')
    @mock.patch('metar_practice.views.MetarCollector')
    def test_practice_post_form_error_question_does_not_exist(self, mock_metar_collector, mock_question_collector):
        instance_mock_metar_collector = mock_metar_collector.return_value
        instance_mock_question_collector = mock_question_collector.return_value
        instance_mock_metar_collector.get_random_airport.return_value = self.db_airport
        instance_mock_metar_collector.get_raw_metar.return_value = (200, self.db_metar)
        instance_mock_question_collector.generate_questions.return_value = self.db_questions[:self.QUESTION_SAMPLE_COUNT]
        session = self.client.session
        session['status'] = 200
        session['airport'] = model_to_dict(self.db_airport)
        session['metar'] = self.metar_json
        session['questions'] = [self.helper_question_to_dict(db_question) for db_question in self.db_questions][1:self.QUESTION_SAMPLE_COUNT:]
        session['api'] = {'timeout' : False, 'end_timeout' : None}
        session['previous_question'] = self.helper_question_to_dict(self.db_questions[0])
        session.save()
        self.db_questions[0].delete()
        description = 'The ICAO is incorrectly saying EGLL.'
        form = {'description': description}
        response = self.client.post(reverse('practice'), form, follow=True)
        self.assertRaises(Question.DoesNotExist)
        try:
            db_report = Report.objects.get(description=description)
            self.fail()
        except Report.DoesNotExist:
            pass
        session = self.client.session
        instance_mock_metar_collector.get_random_airport.assert_not_called()
        instance_mock_metar_collector.get_raw_metar.assert_not_called()
        instance_mock_question_collector.generate_questions.assert_not_called()
        self.assertEqual(session['status'], 200)
        self.assertEqual(session['airport'], model_to_dict(self.db_airport))
        self.assertEqual(session['metar'], self.metar_json)
        self.assertEqual(session['questions'], [self.helper_question_to_dict(db_question) for db_question in self.db_questions][2:self.QUESTION_SAMPLE_COUNT:])
        self.assertEqual(session['api'], {'timeout' : False, 'end_timeout' : None})
        self.assertEqual(session['previous_question'], self.helper_question_to_dict(self.db_questions[1]))
        try:
            self.assertEqual(session['logged'], 'Thank you. Your issue has been logged.')
            self.fail()
        except KeyError:
            pass
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['status'], 200)
        self.assertEquals(response.context['airport'], model_to_dict(self.db_airport))
        self.assertEquals(response.context['metar'], self.metar_json)
        self.assertEquals(response.context['question'], self.helper_question_to_dict(self.db_questions[1]))
        self.assertEquals(response.context['refresh_needed'], False)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.views.QuestionColllector')
    @mock.patch('metar_practice.views.MetarCollector')
    def test_practice_post_form_error_previous_question_none(self, mock_metar_collector, mock_question_collector):
        instance_mock_metar_collector = mock_metar_collector.return_value
        instance_mock_question_collector = mock_question_collector.return_value
        instance_mock_metar_collector.get_random_airport.return_value = self.db_airport
        instance_mock_metar_collector.get_raw_metar.return_value = (200, self.db_metar)
        instance_mock_question_collector.generate_questions.return_value = self.db_questions[:self.QUESTION_SAMPLE_COUNT]
        session = self.client.session
        session['status'] = 200
        session['airport'] = model_to_dict(self.db_airport)
        session['metar'] = self.metar_json
        session['questions'] = [self.helper_question_to_dict(db_question) for db_question in self.db_questions][1:self.QUESTION_SAMPLE_COUNT:]
        session['api'] = {'timeout' : False, 'end_timeout' : None}
        session['previous_question'] = None
        session.save()
        description = 'The ICAO is incorrectly saying EGLL.'
        form = {'description': description}
        response = self.client.post(reverse('practice'), form, follow=True)
        try:
            db_report = Report.objects.get(description=description,
                                           question=self.db_questions[0])
            self.fail()
        except Report.DoesNotExist:
            pass
        session = self.client.session
        instance_mock_metar_collector.get_random_airport.assert_not_called()
        instance_mock_metar_collector.get_raw_metar.assert_not_called()
        instance_mock_question_collector.generate_questions.assert_not_called()
        self.assertEqual(session['status'], 200)
        self.assertEqual(session['airport'], model_to_dict(self.db_airport))
        self.assertEqual(session['metar'], self.metar_json)
        self.assertEqual(session['questions'], [self.helper_question_to_dict(db_question) for db_question in self.db_questions][2:self.QUESTION_SAMPLE_COUNT:])
        self.assertEqual(session['api'], {'timeout' : False, 'end_timeout' : None})
        self.assertEqual(session['previous_question'], self.helper_question_to_dict(self.db_questions[1]))
        try:
            self.assertEqual(session['logged'], 'Thank you. Your issue has been logged.')
            self.fail()
        except KeyError:
            pass
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], None)
        self.assertEquals(response.context['status'], 200)
        self.assertEquals(response.context['airport'], model_to_dict(self.db_airport))
        self.assertEquals(response.context['metar'], self.metar_json)
        self.assertEquals(response.context['question'], self.helper_question_to_dict(self.db_questions[1]))
        self.assertEquals(response.context['refresh_needed'], False)
        self.assertEquals(type(response.context['report_form']), ReportForm)


    @mock.patch('metar_practice.views.QuestionColllector')
    @mock.patch('metar_practice.views.MetarCollector')
    def test_practice_logged_form(self, mock_metar_collector, mock_question_collector):
        instance_mock_metar_collector = mock_metar_collector.return_value
        instance_mock_question_collector = mock_question_collector.return_value
        instance_mock_metar_collector.get_random_airport.return_value = self.db_airport
        instance_mock_metar_collector.get_raw_metar.return_value = (200, self.db_metar)
        instance_mock_question_collector.generate_questions.return_value = self.db_questions[:self.QUESTION_SAMPLE_COUNT]
        session = self.client.session
        session['status'] = 200
        session['airport'] = model_to_dict(self.db_airport)
        session['metar'] = self.metar_json
        session['questions'] = [self.helper_question_to_dict(db_question) for db_question in self.db_questions][1:self.QUESTION_SAMPLE_COUNT:]
        session['api'] = {'timeout' : False, 'end_timeout' : None}
        session['previous_question'] = self.helper_question_to_dict(self.db_questions[0])
        session['logged'] = 'Thank you. Your issue has been logged.'
        session.save()
        response = self.client.get(reverse('practice'))
        session = self.client.session
        instance_mock_metar_collector.get_random_airport.assert_not_called()
        instance_mock_metar_collector.get_raw_metar.assert_not_called()
        instance_mock_question_collector.generate_questions.assert_not_called()
        self.assertEqual(session['status'], 200)
        self.assertEqual(session['airport'], model_to_dict(self.db_airport))
        self.assertEqual(session['metar'], self.metar_json)
        self.assertEqual(session['questions'], [self.helper_question_to_dict(db_question) for db_question in self.db_questions][2:self.QUESTION_SAMPLE_COUNT:])
        self.assertEqual(session['api'], {'timeout' : False, 'end_timeout' : None})
        self.assertEqual(session['previous_question'], self.helper_question_to_dict(self.db_questions[1]))
        self.assertEqual(session['logged'], None)
        self.assertTemplateUsed(response, 'base.html')
        self.assertTemplateUsed(response, 'metar_practice/sub_base.html')
        self.assertTemplateUsed(response, 'metar_practice/practice.html')
        self.assertEquals(response.context['title'], 'METAR Practice')
        self.assertEquals(response.context['logged'], 'Thank you. Your issue has been logged.')
        self.assertEquals(response.context['status'], 200)
        self.assertEquals(response.context['airport'], model_to_dict(self.db_airport))
        self.assertEquals(response.context['metar'], self.metar_json)
        self.assertEquals(response.context['question'], self.helper_question_to_dict(self.db_questions[1]))
        self.assertEquals(response.context['refresh_needed'], False)
        self.assertEquals(type(response.context['report_form']), ReportForm)
