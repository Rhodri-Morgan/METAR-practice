from django import db
import mock
from django.test import TestCase

import metar_practice.pull_metar_data as pull_metar_data

from metar_practice.models import Airport
from metar_practice.models import Metar
from metar_practice.models import Question
from metar_practice.models import Answer

from metar_practice.enums import QuestionType

import os
import json


class TestPullMetarData(TestCase):

    def helper_extract_json(self, path):
        extracted_json = None
        with open(path) as f:
            extracted_json = json.load(f)
        return json.dumps(extracted_json)


    def helper_create_db_airport(self):
        db_airport = Airport(name='John F Kennedy International Airport',
                             city='New York',
                             country='United States',
                             icao='KJFK',
                             latitude='40.63980103',
                             longitude='-73.77890015')
        db_airport.full_clean()
        db_airport.save()
        return db_airport


    def helper_create_db_metar(self, db_airport, metar_path):
        db_metar = Metar(metar_json=self.helper_extract_json(metar_path),
                         airport=db_airport)
        db_metar.full_clean()
        db_metar.save()
        return db_metar


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


    def helper_get_db_answers(self, db_questions):
        db_answers = []
        for db_question in db_questions:
            for found_db_answer in db_question.answers.all():
                if found_db_answer not in db_answers:
                    db_answers.append(found_db_answer)
        return db_answers


    @mock.patch('metar_practice.question_collector.QuestionCollector.generate_questions')
    @mock.patch('metar_practice.metar_collector.MetarCollector.get_raw_metar')
    @mock.patch('metar_practice.metar_collector.MetarCollector.get_random_airport')
    def test_pull_metar_data(self,
                             mock_metar_collector_random_airport,
                             mock_metar_collector_raw_metar,
                             mock_question_collector_generate_questions):
        db_airport = self.helper_create_db_airport()
        status = 200
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'pull_metar_data', 'sample_metar_KJFK_1.json')
        db_metar = self.helper_create_db_metar(db_airport, metar_path)
        db_questions = []
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the airport ICAO?', ['KJFK'], QuestionType.AIRPORT))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is time was this METAR report made?', ['1551 ZULU'], QuestionType.TIME))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the wind direction?', ['350 degrees'], QuestionType.WIND_DIRECTION))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the wind speed?', ['21 kt'], QuestionType.WIND_SPEED))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the wind gusting to?', ['The wind is not currently gusting.'], QuestionType.WIND_GUST))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the altimeter?', ['29.66 inHg'], QuestionType.ALTIMETER))
        mock_metar_collector_random_airport.return_value = db_airport
        mock_metar_collector_raw_metar.return_value = (status, db_metar)
        mock_question_collector_generate_questions.return_value = db_questions
        pull_metar_data.hour_pull_count = 1
        pull_metar_data.database_question_limit = 100
        pull_metar_data.main()
        mock_metar_collector_random_airport.assert_called_once()
        mock_metar_collector_raw_metar.assert_called_once()
        mock_question_collector_generate_questions.assert_called_once()


    @mock.patch('metar_practice.question_collector.QuestionCollector.generate_questions')
    @mock.patch('metar_practice.metar_collector.MetarCollector.get_raw_metar')
    @mock.patch('metar_practice.metar_collector.MetarCollector.get_random_airport')
    def test_pull_metar_data_none_airport(self,
                                          mock_metar_collector_random_airport,
                                          mock_metar_collector_raw_metar,
                                          mock_question_collector_generate_questions):
        db_airport = self.helper_create_db_airport()
        status = 200
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'pull_metar_data', 'sample_metar_KJFK_1.json')
        db_metar = self.helper_create_db_metar(db_airport, metar_path)
        db_questions = []
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the airport ICAO?', ['KJFK'], QuestionType.AIRPORT))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is time was this METAR report made?', ['1551 ZULU'], QuestionType.TIME))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the wind direction?', ['350 degrees'], QuestionType.WIND_DIRECTION))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the wind speed?', ['21 kt'], QuestionType.WIND_SPEED))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the wind gusting to?', ['The wind is not currently gusting.'], QuestionType.WIND_GUST))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the altimeter?', ['29.66 inHg'], QuestionType.ALTIMETER))
        mock_metar_collector_random_airport.return_value = None
        mock_metar_collector_raw_metar.return_value = (status, db_metar)
        mock_question_collector_generate_questions.return_value = db_questions
        pull_metar_data.hour_pull_count = 1
        pull_metar_data.database_question_limit = 100
        pull_metar_data.main()
        mock_metar_collector_random_airport.assert_called_once()
        mock_metar_collector_raw_metar.assert_not_called()
        mock_question_collector_generate_questions.assert_not_called()


    @mock.patch('metar_practice.question_collector.QuestionCollector.generate_questions')
    @mock.patch('metar_practice.metar_collector.MetarCollector.get_raw_metar')
    @mock.patch('metar_practice.metar_collector.MetarCollector.get_random_airport')
    def test_pull_metar_data_none_200_status(self,
                                             mock_metar_collector_random_airport,
                                             mock_metar_collector_raw_metar,
                                             mock_question_collector_generate_questions):
        db_airport = self.helper_create_db_airport()
        status = 400
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'pull_metar_data', 'sample_metar_KJFK_1.json')
        db_metar = self.helper_create_db_metar(db_airport, metar_path)
        db_questions = []
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the airport ICAO?', ['KJFK'], QuestionType.AIRPORT))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is time was this METAR report made?', ['1551 ZULU'], QuestionType.TIME))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the wind direction?', ['350 degrees'], QuestionType.WIND_DIRECTION))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the wind speed?', ['21 kt'], QuestionType.WIND_SPEED))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the wind gusting to?', ['The wind is not currently gusting.'], QuestionType.WIND_GUST))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the altimeter?', ['29.66 inHg'], QuestionType.ALTIMETER))
        mock_metar_collector_random_airport.return_value = db_airport
        mock_metar_collector_raw_metar.return_value = (status, db_metar)
        mock_question_collector_generate_questions.return_value = db_questions
        pull_metar_data.hour_pull_count = 1
        pull_metar_data.database_question_limit = 100
        pull_metar_data.main()
        mock_metar_collector_random_airport.assert_called_once()
        mock_metar_collector_raw_metar.assert_called_once()
        mock_question_collector_generate_questions.assert_not_called()


    @mock.patch('metar_practice.question_collector.QuestionCollector.generate_questions')
    @mock.patch('metar_practice.metar_collector.MetarCollector.get_raw_metar')
    @mock.patch('metar_practice.metar_collector.MetarCollector.get_random_airport')
    def test_pull_metar_data_none_db_metar(self,
                                           mock_metar_collector_random_airport,
                                           mock_metar_collector_raw_metar,
                                           mock_question_collector_generate_questions):
        db_airport = self.helper_create_db_airport()
        status = 200
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'pull_metar_data', 'sample_metar_KJFK_1.json')
        db_metar = self.helper_create_db_metar(db_airport, metar_path)
        db_questions = []
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the airport ICAO?', ['KJFK'], QuestionType.AIRPORT))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is time was this METAR report made?', ['1551 ZULU'], QuestionType.TIME))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the wind direction?', ['350 degrees'], QuestionType.WIND_DIRECTION))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the wind speed?', ['21 kt'], QuestionType.WIND_SPEED))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the wind gusting to?', ['The wind is not currently gusting.'], QuestionType.WIND_GUST))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the altimeter?', ['29.66 inHg'], QuestionType.ALTIMETER))
        mock_metar_collector_random_airport.return_value = db_airport
        mock_metar_collector_raw_metar.return_value = (status, None)
        mock_question_collector_generate_questions.return_value = db_questions
        pull_metar_data.hour_pull_count = 1
        pull_metar_data.database_question_limit = 100
        pull_metar_data.main()
        mock_metar_collector_random_airport.assert_called_once()
        mock_metar_collector_raw_metar.assert_called_once()
        mock_question_collector_generate_questions.assert_not_called()


    @mock.patch('metar_practice.question_collector.QuestionCollector.generate_questions')
    @mock.patch('metar_practice.metar_collector.MetarCollector.get_raw_metar')
    @mock.patch('metar_practice.metar_collector.MetarCollector.get_random_airport')
    def test_pull_metar_data_non_overflow(self,
                                         mock_metar_collector_random_airport,
                                         mock_metar_collector_raw_metar,
                                         mock_question_collector_generate_questions):
        db_airport = self.helper_create_db_airport()
        status = 200
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'pull_metar_data', 'sample_metar_KJFK_1.json')
        db_metar = self.helper_create_db_metar(db_airport, metar_path)
        db_questions = []
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the airport ICAO?', ['KJFK'], QuestionType.AIRPORT))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is time was this METAR report made?', ['1551 ZULU'], QuestionType.TIME))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the wind direction?', ['350 degrees'], QuestionType.WIND_DIRECTION))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the wind speed?', ['21 kt'], QuestionType.WIND_SPEED))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the wind gusting to?', ['The wind is not currently gusting.'], QuestionType.WIND_GUST))
        db_questions.append(self.helper_create_db_question(db_metar, 'What is the altimeter?', ['29.66 inHg'], QuestionType.ALTIMETER))
        db_answers = self.helper_get_db_answers(db_questions)
        mock_metar_collector_random_airport.return_value = db_airport
        mock_metar_collector_raw_metar.return_value = (status, db_metar)
        mock_question_collector_generate_questions.return_value = db_questions
        pull_metar_data.hour_pull_count = 1
        pull_metar_data.database_question_limit = 100
        pull_metar_data.main()
        self.assertEquals(len(Metar.objects.all()), 1)
        self.assertEquals(db_metar, Metar.objects.all().first())
        self.assertEquals(len(Question.objects.all()), len(db_questions))
        for db_question in db_questions:
            self.assertTrue(db_question in Question.objects.all())
        self.assertEquals(len(db_answers), len(Answer.objects.all()))
        for db_answer in db_answers:
            self.assertTrue(db_answer in Answer.objects.all())
        mock_metar_collector_random_airport.assert_called_once()
        mock_metar_collector_raw_metar.assert_called_once()
        mock_question_collector_generate_questions.assert_called_once()


    @mock.patch('metar_practice.models.Metar.objects.order_by')
    @mock.patch('metar_practice.question_collector.QuestionCollector.generate_questions')
    @mock.patch('metar_practice.metar_collector.MetarCollector.get_raw_metar')
    @mock.patch('metar_practice.metar_collector.MetarCollector.get_random_airport')
    def test_pull_metar_data_overflow_all_answers_overlap(self,
                                                          mock_metar_collector_random_airport,
                                                          mock_metar_collector_raw_metar,
                                                          mock_question_collector_generate_questions,
                                                          mock_models_metar_order_by):
        db_airport = self.helper_create_db_airport()
        status = 200
        metar_path_1 = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'pull_metar_data', 'sample_metar_KJFK_1.json')
        metar_path_2 = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'pull_metar_data', 'sample_metar_KJFK_2.json')
        db_metar_1 = self.helper_create_db_metar(db_airport, metar_path_1)
        db_metar_2 = self.helper_create_db_metar(db_airport, metar_path_2)
        db_questions_1 = []
        db_questions_1.append(self.helper_create_db_question(db_metar_1, 'What is the airport ICAO?', ['KJFK'], QuestionType.AIRPORT))
        db_questions_1.append(self.helper_create_db_question(db_metar_1, 'What is the wind gusting to?', ['The wind is not currently gusting.'], QuestionType.WIND_GUST))
        db_questions_1.append(self.helper_create_db_question(db_metar_1, 'What is the visibility?', ['10 sm'], QuestionType.VISIBILITY))
        db_questions_2 = []
        db_questions_2.append(self.helper_create_db_question(db_metar_2, 'What is the airport ICAO?', ['KJFK'], QuestionType.AIRPORT))
        db_questions_2.append(self.helper_create_db_question(db_metar_2, 'What is the wind gusting to?', ['The wind is not currently gusting.'], QuestionType.WIND_GUST))
        db_questions_2.append(self.helper_create_db_question(db_metar_2, 'What is the visibility?', ['10 sm'], QuestionType.VISIBILITY))
        db_answers = self.helper_get_db_answers(db_questions_2)
        mock_metar_collector_random_airport.return_value = db_airport
        mock_metar_collector_raw_metar.side_effect = [(status, db_metar_1), (status, db_metar_2)]
        mock_question_collector_generate_questions.side_effect = [db_questions_1, db_questions_2]
        mock_models_metar_order_by.side_effect = [Metar.objects.filter(pk=db_metar_1.pk)]
        pull_metar_data.hour_pull_count = 2
        pull_metar_data.database_question_limit =  3
        pull_metar_data.main()
        self.assertEquals(len(Metar.objects.all()), 1)
        self.assertEquals(db_metar_2, Metar.objects.all().first())
        self.assertEquals(len(Question.objects.all()), len(db_questions_2))
        for db_question in db_questions_2:
            self.assertTrue(db_question in Question.objects.all())
        self.assertEquals(len(db_answers), len(Answer.objects.all()))
        for db_answer in db_answers:
            self.assertTrue(db_answer in Answer.objects.all())
        mock_models_metar_order_by.assert_called_once()
        self.assertEquals(mock_metar_collector_random_airport.call_count, 2)
        self.assertEquals(mock_metar_collector_raw_metar.call_count, 2)
        self.assertEquals(mock_question_collector_generate_questions.call_count, 2)


    @mock.patch('metar_practice.models.Metar.objects.order_by')
    @mock.patch('metar_practice.question_collector.QuestionCollector.generate_questions')
    @mock.patch('metar_practice.metar_collector.MetarCollector.get_raw_metar')
    @mock.patch('metar_practice.metar_collector.MetarCollector.get_random_airport')
    def test_pull_metar_data_overflow_some_answers_overlap(self,
                                                           mock_metar_collector_random_airport,
                                                           mock_metar_collector_raw_metar,
                                                           mock_question_collector_generate_questions,
                                                           mock_models_metar_order_by):
        db_airport = self.helper_create_db_airport()
        status = 200
        metar_path_1 = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'pull_metar_data', 'sample_metar_KJFK_1.json')
        metar_path_2 = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'pull_metar_data', 'sample_metar_KJFK_2.json')
        db_metar_1 = self.helper_create_db_metar(db_airport, metar_path_1)
        db_metar_2 = self.helper_create_db_metar(db_airport, metar_path_2)
        db_questions_1 = []
        db_questions_1.append(self.helper_create_db_question(db_metar_1, 'What is the airport ICAO?', ['KJFK'], QuestionType.AIRPORT))
        db_questions_1.append(self.helper_create_db_question(db_metar_1, 'What is time was this METAR report made?', ['1551 ZULU'], QuestionType.TIME))
        db_questions_1.append(self.helper_create_db_question(db_metar_1, 'What is the wind direction?', ['350 degrees'], QuestionType.WIND_DIRECTION))
        db_questions_1.append(self.helper_create_db_question(db_metar_1, 'What is the wind speed?', ['21 kt'], QuestionType.WIND_SPEED))
        db_questions_1.append(self.helper_create_db_question(db_metar_1, 'What is the wind gusting to?', ['The wind is not currently gusting.'], QuestionType.WIND_GUST))
        db_questions_1.append(self.helper_create_db_question(db_metar_1, 'What is the altimeter?', ['29.66 inHg'], QuestionType.ALTIMETER))
        db_questions_2 = []
        db_questions_2.append(self.helper_create_db_question(db_metar_2, 'What is the airport ICAO?', ['KJFK'], QuestionType.AIRPORT))
        db_questions_2.append(self.helper_create_db_question(db_metar_2, 'What is time was this METAR report made?', ['1051 ZULU'], QuestionType.TIME))
        db_questions_2.append(self.helper_create_db_question(db_metar_2, 'What is the wind direction?', ['30 degrees'], QuestionType.WIND_DIRECTION))
        db_questions_2.append(self.helper_create_db_question(db_metar_2, 'What is the wind speed?', ['3 kt'], QuestionType.WIND_SPEED))
        db_questions_2.append(self.helper_create_db_question(db_metar_2, 'What is the wind gusting to?', ['The wind is not currently gusting.'], QuestionType.WIND_GUST))
        db_answers = self.helper_get_db_answers(db_questions_2)
        mock_metar_collector_random_airport.return_value = db_airport
        mock_metar_collector_raw_metar.side_effect = [(status, db_metar_1), (status, db_metar_2)]
        mock_question_collector_generate_questions.side_effect = [db_questions_1, db_questions_2]
        mock_models_metar_order_by.side_effect = [Metar.objects.filter(pk=db_metar_1.pk)]
        pull_metar_data.hour_pull_count = 2
        pull_metar_data.database_question_limit =  5
        pull_metar_data.main()
        self.assertEquals(len(Metar.objects.all()), 1)
        self.assertEquals(db_metar_2, Metar.objects.all().first())
        self.assertEquals(len(Question.objects.all()), len(db_questions_2))
        for db_question in db_questions_2:
            self.assertTrue(db_question in Question.objects.all())
        self.assertEquals(len(db_answers), len(Answer.objects.all()))
        for db_answer in db_answers:
            self.assertTrue(db_answer in Answer.objects.all())
        mock_models_metar_order_by.assert_called_once()
        self.assertEquals(mock_metar_collector_random_airport.call_count, 2)
        self.assertEquals(mock_metar_collector_raw_metar.call_count, 2)
        self.assertEquals(mock_question_collector_generate_questions.call_count, 2)


    @mock.patch('metar_practice.models.Metar.objects.order_by')
    @mock.patch('metar_practice.question_collector.QuestionCollector.generate_questions')
    @mock.patch('metar_practice.metar_collector.MetarCollector.get_raw_metar')
    @mock.patch('metar_practice.metar_collector.MetarCollector.get_random_airport')
    def test_pull_metar_data_overflow_none_answers_overlap(self,
                                                           mock_metar_collector_random_airport,
                                                           mock_metar_collector_raw_metar,
                                                           mock_question_collector_generate_questions,
                                                           mock_models_metar_order_by):
        db_airport_1 = self.helper_create_db_airport()
        db_airport_2 = Airport(name='London Heathrow Airport',
                               city='London',
                               country='United Kingdom',
                               icao='EGLL',
                               latitude='51.4706',
                               longitude='-0.461941')
        db_airport_2.full_clean()
        db_airport_2.save()
        status = 200
        metar_path_1 = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'pull_metar_data', 'sample_metar_KJFK_1.json')
        metar_path_2 = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'pull_metar_data', 'sample_metar_EGLL.json')
        db_metar_1 = self.helper_create_db_metar(db_airport_1, metar_path_1)
        db_metar_2 = self.helper_create_db_metar(db_airport_2, metar_path_2)
        db_questions_1 = []
        db_questions_1.append(self.helper_create_db_question(db_metar_1, 'What is the airport ICAO?', ['KJFK'], QuestionType.AIRPORT))
        db_questions_1.append(self.helper_create_db_question(db_metar_1, 'What is time was this METAR report made?', ['1551 ZULU'], QuestionType.TIME))
        db_questions_1.append(self.helper_create_db_question(db_metar_1, 'What is the wind direction?', ['350 degrees'], QuestionType.WIND_DIRECTION))
        db_questions_1.append(self.helper_create_db_question(db_metar_1, 'What is the wind speed?', ['21 kt'], QuestionType.WIND_SPEED))
        db_questions_1.append(self.helper_create_db_question(db_metar_1, 'What is the wind gusting to?', ['The wind is not currently gusting.'], QuestionType.WIND_GUST))
        db_questions_1.append(self.helper_create_db_question(db_metar_1, 'What is the altimeter?', ['29.66 inHg'], QuestionType.ALTIMETER))
        db_questions_2 = []
        db_questions_2.append(self.helper_create_db_question(db_metar_2, 'What is the airport ICAO?', ['EGLL'], QuestionType.AIRPORT))
        db_questions_2.append(self.helper_create_db_question(db_metar_2, 'What is time was this METAR report made?', ['1250 ZULU'], QuestionType.TIME))
        db_questions_2.append(self.helper_create_db_question(db_metar_2, 'What is the wind direction?', ['280 degrees'], QuestionType.WIND_DIRECTION))
        db_questions_2.append(self.helper_create_db_question(db_metar_2, 'What is the wind speed?', ['9 kt'], QuestionType.WIND_SPEED))
        db_questions_2.append(self.helper_create_db_question(db_metar_2, 'What is the reported cloud coverage?', ['Broken Clouds', 'Overcast Clouds'], QuestionType.CLOUD_COVERAGE))
        db_questions_2.append(self.helper_create_db_question(db_metar_2, 'What is the dewpoint?', ['9 C'], QuestionType.DEWPOINT))
        db_questions_2.append(self.helper_create_db_question(db_metar_2, 'What is the visibility?', ['9999 sm'], QuestionType.VISIBILITY))
        db_answers = self.helper_get_db_answers(db_questions_2)
        mock_metar_collector_random_airport.side_effect = [db_airport_1, db_airport_2]
        mock_metar_collector_raw_metar.side_effect = [(status, db_metar_1), (status, db_metar_2)]
        mock_question_collector_generate_questions.side_effect = [db_questions_1, db_questions_2]
        mock_models_metar_order_by.side_effect = [Metar.objects.filter(pk=db_metar_1.pk)]
        pull_metar_data.hour_pull_count = 2
        pull_metar_data.database_question_limit =  8
        pull_metar_data.main()
        self.assertEquals(len(Metar.objects.all()), 1)
        self.assertEquals(db_metar_2, Metar.objects.all().first())
        self.assertEquals(len(Question.objects.all()), len(db_questions_2))
        for db_question in db_questions_2:
            self.assertTrue(db_question in Question.objects.all())
        self.assertEquals(len(db_answers), len(Answer.objects.all()))
        for db_answer in db_answers:
            self.assertTrue(db_answer in Answer.objects.all())
        mock_models_metar_order_by.assert_called_once()
        self.assertEquals(mock_metar_collector_random_airport.call_count, 2)
        self.assertEquals(mock_metar_collector_raw_metar.call_count, 2)
        self.assertEquals(mock_question_collector_generate_questions.call_count, 2)
