from django.test import TestCase
import mock
from unittest.mock import call  # need to import call.

import os
import json
import sys

from enum import Enum
from enum import auto

from metar_practice.question_collector import QuestionColllector
from metar_practice.question_collector import UsuableDataError

from metar_practice.models import Airport
from metar_practice.models import Metar
from metar_practice.models import Answer
from metar_practice.models import Question


class TestCreateDbAnswers(TestCase):

    def setUp(self):
        db_airport = Airport(name='John F Kennedy International Airport',
                             city='New York',
                             country='United States',
                             icao='KJFK',
                             latitude='40.63980103',
                             longitude='-73.77890015')
        db_airport.save()
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        with open(metar_path) as f:
            metar_json = json.load(f)
        db_metar = Metar(metar_json=json.dumps(metar_json),
                         airport=db_airport)
        db_metar.save()
        sample_count = 6
        self.question_collector = QuestionColllector(db_metar, sample_count)


    def get_db_answer(self, text):
        db_answer = None
        try:
            db_answer = Answer.objects.get(text=text)
        except KeyError:
            self.fail()
        return db_answer


    def test_create_db_answers_no_answers(self):
        returned_db_answers = self.question_collector.create_db_answers([])
        self.assertEquals(len(Answer.objects.all()), 0)
        self.assertEquals(len(returned_db_answers), 0)


    def test_create_db_answers_single_does_not_exist(self):
        answer = 'This is a test answer string'
        returned_db_answers = self.question_collector.create_db_answers([answer])
        self.assertRaises(Answer.DoesNotExist)
        self.assertEquals(len(Answer.objects.all()), 1)
        self.assertEquals(len(returned_db_answers), 1)
        self.assertIsNotNone(returned_db_answers[0])
        self.assertEquals(returned_db_answers[0], self.get_db_answer(answer))


    def test_create_db_answers_single_already_exists(self):
        answer = 'This is a test answer string'
        db_answer = Answer(text=answer)
        db_answer.save()
        returned_db_answers = self.question_collector.create_db_answers([answer])
        self.assertEquals(len(Answer.objects.all()), 1)
        self.assertIsNotNone(returned_db_answers[0])
        self.assertIsNotNone(db_answer)
        self.assertEquals(returned_db_answers, [db_answer])
        self.assertEquals(returned_db_answers[0], db_answer)


    def test_create_db_answers_multiple_does_not_exist(self):
        answers = []
        for i in range(1,5):
            answers.append('This is test answer string {}'.format(i))
        returned_db_answers = self.question_collector.create_db_answers(answers.copy())
        self.assertRaises(Answer.DoesNotExist)
        self.assertEquals(len(Answer.objects.all()), len(answers))
        self.assertEquals(len(returned_db_answers), len(answers))
        for returned_db_answer in returned_db_answers:
            self.assertIsNotNone(returned_db_answer)
        for i in range(0, len(answers)):
            self.assertEquals(returned_db_answers[i], self.get_db_answer(answers[i]))


    def test_create_db_answers_multiple_already_exists(self):
        answers = []
        db_answers = []
        for i in range(1,5):
            answers.append('This is test answer string {}'.format(i))
            db_answer = Answer(text=answers[i-1])
            db_answer.save()
            db_answers.append(db_answer)
        returned_db_answers = self.question_collector.create_db_answers(answers.copy())
        self.assertEquals(len(Answer.objects.all()), len(db_answers))
        self.assertEquals(len(returned_db_answers), len(db_answers))
        for returned_db_answer in returned_db_answers:
            self.assertIsNotNone(returned_db_answer)
        for db_answer in db_answers:
            self.assertIsNotNone(db_answer)
        for i in range(0, len(db_answers)):
            self.assertEquals(returned_db_answers[i], db_answers[i])


class TestCreateDbQuestion(TestCase):

    def setUp(self):
        db_airport = Airport(name='John F Kennedy International Airport',
                             city='New York',
                             country='United States',
                             icao='KJFK',
                             latitude='40.63980103',
                             longitude='-73.77890015')
        db_airport.save()
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        with open(metar_path) as f:
            metar_json = json.load(f)
        self.db_metar = Metar(metar_json=json.dumps(metar_json),
                              airport=db_airport)
        self.db_metar.save()
        sample_count = 6
        self.question_collector = QuestionColllector(self.db_metar, sample_count)


    def get_db_question(self, text):
        db_question = None
        try:
            db_question = Question.objects.get(metar=self.db_metar,
                                               text=text)
        except KeyError:
            self.fail()
        return db_question


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_answers')
    def test_create_db_questions_question_does_not_exist(self, mock_question_collector_db_answers):
        answers = []
        db_answers = []
        for i in range(1,5):
            answers.append('This is test answer string {}'.format(i))
            db_answer = Answer(text=answers[i-1])
            db_answer.save()
            db_answers.append(db_answer)
        question = 'This is a test question string'
        mock_question_collector_db_answers.return_value = db_answers
        returned_db_question = self.question_collector.create_db_question(question, answers)
        self.assertRaises(Question.DoesNotExist)
        self.assertEquals(len(Question.objects.all()), 1)
        self.assertIsNotNone(returned_db_question)
        db_question = self.get_db_question(question)
        self.assertEquals(returned_db_question, db_question)
        self.assertEquals(returned_db_question.answers, db_question.answers)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_answers')
    def test_create_db_questions_question_already_exists(self, mock_question_collector_db_answers):
        answers = []
        db_answers = []
        for i in range(1,5):
            answers.append('This is test answer string {}'.format(i))
            db_answer = Answer(text=answers[i-1])
            db_answer.save()
            db_answers.append(db_answer)
        question = 'This is a test question string'
        db_question = Question(metar=self.db_metar,
                               text=question)
        db_question.save()
        [db_question.answers.add(db_answer) for db_answer in db_answers]
        mock_question_collector_db_answers.return_value = db_answers
        returned_db_question = self.question_collector.create_db_question(question, answers)
        self.assertEquals(len(Question.objects.all()), 1)
        self.assertIsNotNone(returned_db_question)
        self.assertEquals(returned_db_question, db_question)


class ModifyJSONChoices(Enum):
    DELETE = auto()
    NONE = None
    EMPTY = ''


class TestGenerateTypeQustion(TestCase):

    def setUp(self):
        self.db_airport = Airport(name='John F Kennedy International Airport',
                                  city='New York',
                                  country='United States',
                                  icao='KJFK',
                                  latitude='40.63980103',
                                  longitude='-73.77890015')
        self.db_airport.save()
        self.sample_count = None
        self.cloud_conversion = {'FEW' : 'few',
                                 'SCT' : 'scattered',
                                 'BKN' : 'broken',
                                 'OVC' : 'overcast'}


    def helper_create_metar_object(self, path, db_airport):
        metar_json = None
        with open(path) as f:
            metar_json = json.load(f)
        db_metar = Metar(metar_json=json.dumps(metar_json),
                         airport=db_airport)
        db_metar.save()
        return db_metar


    def iterate_json(self, json_dict, keys, action):
        if len(keys) == 1:
            if action == ModifyJSONChoices.DELETE:
                del json_dict[keys.pop(0)]
            else:
                json_dict[keys.pop(0)] = action.value
        else:
            self.iterate_json(json_dict[keys.pop(0)], keys, action)


    def helper_create_modified_metar_object(self, path, db_airport, keys, action):
        metar_json = None
        with open(path) as f:
            metar_json = json.load(f)

        self.iterate_json(metar_json, keys, action)

        db_metar = Metar(metar_json=json.dumps(metar_json),
                         airport=db_airport)
        db_metar.save()
        return db_metar


    def helper_create_db_question(self, db_metar, question_text, answers_text):
        db_answers = []
        for answer_text in answers_text:
            db_answer = Answer(text=answer_text)
            db_answer.save()
            db_answers.append(db_answer)
        db_question = Question(metar=db_metar,
                               text=question_text)
        db_question.save()
        [db_question.answers.add(db_answer) for db_answer in db_answers]
        return db_question


    def helper_create_db_questions(self, db_metar, questions_answers_text):
        db_questions = []
        for question_text, answer_text in questions_answers_text:
            db_answer = Answer(text=answer_text)
            db_answer.save()
            db_question = Question(metar=db_metar,
                                   text=question_text)
            db_question.save()
            db_question.answers.add(db_answer)
            db_questions.append(db_question)
        return db_questions


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_airport_question(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        question_text = 'What is the airport ICAO?'
        answer_text = 'KJFK'
        db_question = self.helper_create_db_question(db_metar, question_text, [answer_text])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_airport_question()
        mock_question_collector_db_question.assert_called_once_with(question_text, [answer_text])
        self.assertEquals(question_collector.questions['airport'], db_question)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_airport_question_station_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['station'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_airport_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['airport']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_airport_question_station_empty(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['station'], ModifyJSONChoices.EMPTY)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_airport_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['airport']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_airport_question_station_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['station'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_airport_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['airport']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_time_question(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        question_text = 'What is time was this METAR report made?'
        answer_text = '1551 ZULU'
        db_question = self.helper_create_db_question(db_metar, question_text, [answer_text])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_time_question()
        mock_question_collector_db_question.assert_called_once_with(question_text, [answer_text])
        self.assertEquals(question_collector.questions['time'], db_question)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_time_question_time_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['time', 'repr'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_time_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['time']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_time_question_time_empty(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['time', 'repr'], ModifyJSONChoices.EMPTY)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_time_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['time']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_time_question_time_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['time', 'repr'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_time_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['time']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_wind_direction_question(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        question_text = 'What is the wind direction?'
        answer_text = '350 degrees'
        db_question = self.helper_create_db_question(db_metar, question_text, [answer_text])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_wind_direction_question()
        mock_question_collector_db_question.assert_called_once_with(question_text, [answer_text])
        self.assertEquals(question_collector.questions['wind_direction'], db_question)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_wind_direction_question_wind_direction_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['wind_direction', 'value'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_wind_direction_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['wind_direction']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_wind_direction_question_wind_direction_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['wind_direction', 'value'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_wind_direction_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['wind_direction']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_wind_speed_question(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        question_text = 'What is the wind speed?'
        answer_text = '21 kt'
        db_question = self.helper_create_db_question(db_metar, question_text, [answer_text])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_wind_speed_question()
        mock_question_collector_db_question.assert_called_once_with(question_text, [answer_text])
        self.assertEquals(question_collector.questions['wind_speed'], db_question)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_wind_speed_question_wind_speed_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['wind_speed', 'value'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_wind_speed_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['wind_speed']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_wind_speed_question_units_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'wind_speed'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_wind_speed_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['wind_speed']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_wind_speed_question_units_empty(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'wind_speed'], ModifyJSONChoices.EMPTY)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_wind_speed_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['wind_speed']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_wind_speed_question_wind_speed_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['wind_speed', 'value'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_wind_speed_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['wind_speed']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_wind_speed_question_units_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'wind_speed'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_wind_speed_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['wind_speed']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_wind_gust_question(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        question_text = 'What is the wind gusting to?'
        answer_text = '29 kt'
        db_question = self.helper_create_db_question(db_metar, question_text, [answer_text])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_wind_gust_question()
        mock_question_collector_db_question.assert_called_once_with(question_text, [answer_text])
        self.assertEquals(question_collector.questions['wind_gust'], db_question)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_wind_gust_question_no_gusts(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['wind_gust'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        question_text = 'What is the wind gusting to?'
        answer_text = 'The wind is not currently gusting.'
        db_question = self.helper_create_db_question(db_metar, question_text, [answer_text])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_wind_gust_question()
        mock_question_collector_db_question.assert_called_once_with(question_text, [answer_text])
        self.assertEquals(question_collector.questions['wind_gust'], db_question)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_wind_gust_question_units_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'wind_speed'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_wind_gust_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['wind_gust']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_wind_gust_question_units_empty(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'wind_speed'], ModifyJSONChoices.EMPTY)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_wind_gust_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['wind_gust']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_wind_gust_question_wind_gust_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['wind_gust'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_wind_gust_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['wind_gust']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_wind_gust_question_units_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'wind_speed'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_wind_gust_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['wind_gust']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_altimeter_question(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        question_text = 'What is the altimeter?'
        answer_text = '29.66 inHg'
        db_question = self.helper_create_db_question(db_metar, question_text, [answer_text])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_altimeter_question()
        mock_question_collector_db_question.assert_called_once_with(question_text, [answer_text])
        self.assertEquals(question_collector.questions['altimeter'], db_question)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_altimeter_question_altimeter_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['altimeter', 'value'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_altimeter_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['altimeter']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_altimeter_question_units_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'altimeter'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_altimeter_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['altimeter']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_altimeter_question_units_empty(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'altimeter'], ModifyJSONChoices.EMPTY)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_altimeter_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['altimeter']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_altimiter_question_altimeter_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['altimeter', 'value'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_altimeter_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['altimeter']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_altimeter_question_units_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'altimeter'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_altimeter_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['altimeter']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_temperature_question(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        question_text = 'What is the temperature?'
        answer_text = '10 C'
        db_question = self.helper_create_db_question(db_metar, question_text, [answer_text])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_temperature_question()
        mock_question_collector_db_question.assert_called_once_with(question_text, [answer_text])
        self.assertEquals(question_collector.questions['temperature'], db_question)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_temperature_question_temperature_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['temperature', 'value'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_temperature_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['temperature']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_temperature_question_units_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'temperature'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_temperature_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['temperature']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_temperature_question_units_empty(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'temperature'], ModifyJSONChoices.EMPTY)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_temperature_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['temperature']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_temperature_question_temperature_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['temperature', 'value'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_temperature_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['temperature']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_temperature_question_units_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'temperature'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_temperature_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['temperature']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_dewpoint_question(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        question_text = 'What is the dewpoint?'
        answer_text = '7 C'
        db_question = self.helper_create_db_question(db_metar, question_text, [answer_text])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_dewpoint_question()
        mock_question_collector_db_question.assert_called_once_with(question_text, [answer_text])
        self.assertEquals(question_collector.questions['dewpoint'], db_question)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_dewpoint_question_dewpoint_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['dewpoint', 'value'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_dewpoint_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['dewpoint']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_dewpoint_question_units_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'temperature'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_dewpoint_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['dewpoint']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_dewpoint_question_units_empty(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'temperature'], ModifyJSONChoices.EMPTY)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_dewpoint_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['dewpoint']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_dewpoint_question_dewpoint_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['dewpoint', 'value'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_dewpoint_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['dewpoint']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_dewpoint_question_units_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'temperature'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_dewpoint_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['dewpoint']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_visibility_question(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        question_text = 'What is the visibility?'
        answer_text = '10 sm'
        db_question = self.helper_create_db_question(db_metar, question_text, [answer_text])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_visibility_question()
        mock_question_collector_db_question.assert_called_once_with(question_text, [answer_text])
        self.assertEquals(question_collector.questions['visibility'], db_question)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_visibility_question_visibility_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['visibility', 'value'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_visibility_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['visibility']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_visibility_question_units_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'visibility'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_visibility_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['visibility']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_visibility_question_units_empty(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'visibility'], ModifyJSONChoices.EMPTY)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_visibility_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['visibility']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_visibility_question_visibility_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['visibility', 'value'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_visibility_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['visibility']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_visibility_question_units_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'visibility'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_visibility_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['visibility']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_coverage_question(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        question_text = 'What is the reported cloud coverage?'
        answers_text = ['Few Clouds', 'Broken Clouds', 'Overcast Clouds']
        db_question = self.helper_create_db_question(db_metar, question_text, answers_text)
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_coverage_question()
        mock_question_collector_db_question.assert_called_once_with(question_text, answers_text)
        self.assertEquals(question_collector.questions['cloud_coverage'], db_question)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_coverage_question_all(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar_cloud_coverage_all.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        question_text = 'What is the reported cloud coverage?'
        answers_text = ['Sky Clear',
                        'NIL Cloud Detected',
                        'No Clouds Below 12,000 ft',
                        'No Significant Cloud',
                        'Few Clouds',
                        'Scattered Clouds',
                        'Broken Clouds',
                        'Overcast Clouds',
                        'Vertical Visability Warning']
        db_question = self.helper_create_db_question(db_metar, question_text, answers_text)
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_coverage_question()
        mock_question_collector_db_question.assert_called_once_with(question_text, answers_text)
        self.assertEquals(question_collector.questions['cloud_coverage'], db_question)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_coverage_question_clouds_duplicates(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar_cloud_coverage_duplicates.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        question_text = 'What is the reported cloud coverage?'
        answers_text = ['Few Clouds', 'Scattered Clouds', 'Broken Clouds', 'Overcast Clouds']
        db_question = self.helper_create_db_question(db_metar, question_text, answers_text)
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_coverage_question()
        mock_question_collector_db_question.assert_called_once_with(question_text, answers_text)
        self.assertEquals(question_collector.questions['cloud_coverage'], db_question)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_coverage_question_cloud_type_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['clouds', 0, 'type'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_coverage_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['cloud_coverage']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_coverage_question_clouds_empty(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar_clouds_empty.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_coverage_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['cloud_coverage']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_coverage_question_cloud_type_empty(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['clouds', 0, 'type'], ModifyJSONChoices.EMPTY)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_coverage_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['cloud_coverage']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_coverage_question_clouds_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['clouds'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_coverage_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['cloud_coverage']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_coverage_question_cloud_type_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['clouds', 0, 'type'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_coverage_question()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['cloud_coverage']
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_height_question_few(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar_cloud_coverage_duplicates.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        cloud = 'FEW'
        question_text = 'What is the height of the {0} clouds?'.format(self.cloud_conversion[cloud])
        answers_text = ['2400 ft', '5000 ft']
        db_question = self.helper_create_db_question(db_metar, question_text, answers_text)
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_height_question(cloud)
        mock_question_collector_db_question.assert_called_once_with(question_text, answers_text)
        self.assertEquals(question_collector.questions['cloud_{0}_heights'.format(self.cloud_conversion[cloud])], db_question)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_height_question_scattered(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar_cloud_coverage_duplicates.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        cloud = 'SCT'
        question_text = 'What is the height of the {0} clouds?'.format(self.cloud_conversion[cloud])
        answers_text = ['9800 ft']
        db_question = self.helper_create_db_question(db_metar, question_text, answers_text)
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_height_question(cloud)
        mock_question_collector_db_question.assert_called_once_with(question_text, answers_text)
        self.assertEquals(question_collector.questions['cloud_{0}_heights'.format(self.cloud_conversion[cloud])], db_question)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_height_question_broken(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar_cloud_coverage_duplicates.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        cloud = 'BKN'
        question_text = 'What is the height of the {0} clouds?'.format(self.cloud_conversion[cloud])
        answers_text = ['3600 ft']
        db_question = self.helper_create_db_question(db_metar, question_text, answers_text)
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_height_question(cloud)
        mock_question_collector_db_question.assert_called_once_with(question_text, answers_text)
        self.assertEquals(question_collector.questions['cloud_{0}_heights'.format(self.cloud_conversion[cloud])], db_question)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_height_question_overcast(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar_cloud_coverage_duplicates.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        cloud = 'OVC'
        question_text = 'What is the height of the {0} clouds?'.format(self.cloud_conversion[cloud])
        answers_text = ['4600 ft', '7000 ft', '9000 ft']
        db_question = self.helper_create_db_question(db_metar, question_text, answers_text)
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_height_question(cloud)
        mock_question_collector_db_question.assert_called_once_with(question_text, answers_text)
        self.assertEquals(question_collector.questions['cloud_{0}_heights'.format(self.cloud_conversion[cloud])], db_question)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_height_question_clouds_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['clouds'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        cloud = 'FEW'
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_height_question(cloud)
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['cloud_{0}_heights'.format(self.cloud_conversion[cloud])]
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_height_question_cloud_type_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['clouds', 0, 'type'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        cloud = 'FEW'
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_height_question(cloud)
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['cloud_{0}_heights'.format(self.cloud_conversion[cloud])]
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_height_question_cloud_altitude_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['clouds', 0, 'altitude'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        cloud = 'FEW'
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_height_question(cloud)
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['cloud_{0}_heights'.format(self.cloud_conversion[cloud])]
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_height_question_cloud_units_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'altitude'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        cloud = 'FEW'
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_height_question(cloud)
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['cloud_{0}_heights'.format(self.cloud_conversion[cloud])]
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_height_question_clouds_empty(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar_clouds_empty.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        cloud = 'FEW'
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_height_question(cloud)
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['cloud_{0}_heights'.format(self.cloud_conversion[cloud])]
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_height_question_cloud_type_empty(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['clouds', 0, 'type'], ModifyJSONChoices.EMPTY)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        cloud = 'FEW'
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_height_question(cloud)
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['cloud_{0}_heights'.format(self.cloud_conversion[cloud])]
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_height_question_cloud_units_empty(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'altitude'], ModifyJSONChoices.EMPTY)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        cloud = 'FEW'
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_height_question(cloud)
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        try:
            stored_question = question_collector.questions['cloud_{0}_heights'.format(self.cloud_conversion[cloud])]
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_height_question_clouds_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['clouds'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        cloud = 'FEW'
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_height_question(cloud)
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['cloud_{0}_heights'.format(self.cloud_conversion[cloud])]
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_height_question_cloud_type_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['clouds', 0, 'type'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        cloud = 'FEW'
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_height_question(cloud)
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['cloud_{0}_heights'.format(self.cloud_conversion[cloud])]
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_height_question_cloud_altitude_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['clouds', 0, 'altitude'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        cloud = 'FEW'
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_height_question(cloud)
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['cloud_{0}_heights'.format(self.cloud_conversion[cloud])]
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_height_question_cloud_units_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'altitude'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        cloud = 'FEW'
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_height_question(cloud)
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        try:
            stored_question = question_collector.questions['cloud_{0}_heights'.format(self.cloud_conversion[cloud])]
            self.fail()
        except KeyError:
            pass


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_ceiling_question(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar_cloud_coverage_duplicates.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        questions_answers_text = [('What kind of clouds have a ceiling of 2400 ft?', 'Few'),
                                  ('What kind of clouds have a ceiling of 5000 ft?', 'Few'),
                                  ('What kind of clouds have a ceiling of 9800 ft?', 'Scattered'),
                                  ('What kind of clouds have a ceiling of 3600 ft?', 'Broken'),
                                  ('What kind of clouds have a ceiling of 4600 ft?', 'Overcast'),
                                  ('What kind of clouds have a ceiling of 9000 ft?', 'Overcast'),
                                  ('What kind of clouds have a ceiling of 7000 ft?', 'Overcast')]
        db_questions = self.helper_create_db_questions(db_metar, questions_answers_text)
        mock_question_collector_db_question.side_effect = db_questions
        question_collector.generate_cloud_ceiling_questions()
        self.assertEquals(mock_question_collector_db_question.call_count, len(questions_answers_text))
        mock_question_collector_db_question.assert_has_calls([call(question_text, [answer_text]) for question_text, answer_text in questions_answers_text])
        for i in range(0, len(questions_answers_text)):
            self.assertEquals(question_collector.questions['cloud_{0}_ceiling_{1}'.format(questions_answers_text[i][1].lower(), i)], db_questions[i])


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_ceiling_question_cloud_type_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['clouds', 0, 'type'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        questions_answers_text = [('What kind of clouds have a ceiling of 3600 ft?', 'Broken'),
                                  ('What kind of clouds have a ceiling of 4600 ft?', 'Overcast')]
        db_questions = self.helper_create_db_questions(db_metar, questions_answers_text)
        mock_question_collector_db_question.side_effect = db_questions
        question_collector.generate_cloud_ceiling_questions()
        self.assertRaises(UsuableDataError)
        self.assertEquals(mock_question_collector_db_question.call_count, len(questions_answers_text))
        mock_question_collector_db_question.assert_has_calls([call(question_text, [answer_text]) for question_text, answer_text in questions_answers_text])
        for i in range(0, len(questions_answers_text)):
            self.assertEquals(question_collector.questions['cloud_{0}_ceiling_{1}'.format(questions_answers_text[i][1].lower(), i)], db_questions[i])


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_ceiling_question_cloud_altitude_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['clouds', 1, 'altitude'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        questions_answers_text = [('What kind of clouds have a ceiling of 2400 ft?', 'Few'),
                                  ('What kind of clouds have a ceiling of 4600 ft?', 'Overcast')]
        db_questions = self.helper_create_db_questions(db_metar, questions_answers_text)
        mock_question_collector_db_question.side_effect = db_questions
        question_collector.generate_cloud_ceiling_questions()
        self.assertRaises(UsuableDataError)
        self.assertEquals(mock_question_collector_db_question.call_count, len(questions_answers_text))
        mock_question_collector_db_question.assert_has_calls([call(question_text, [answer_text]) for question_text, answer_text in questions_answers_text])
        for i in range(0, len(questions_answers_text)):
            self.assertEquals(question_collector.questions['cloud_{0}_ceiling_{1}'.format(questions_answers_text[i][1].lower(), i)], db_questions[i])


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_ceiling_question_cloud_units_none(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'altitude'], ModifyJSONChoices.NONE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_ceiling_questions()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        self.assertEquals(len(question_collector.questions), 0)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_ceiling_question_clouds_empty(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar_clouds_empty.json')
        db_metar = self.helper_create_metar_object(metar_path, self.db_airport)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_ceiling_questions()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        self.assertEquals(len(question_collector.questions), 0)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_ceiling_question_cloud_type_empty(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['clouds', 0, 'type'], ModifyJSONChoices.EMPTY)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        questions_answers_text = [('What kind of clouds have a ceiling of 3600 ft?', 'Broken'),
                                  ('What kind of clouds have a ceiling of 4600 ft?', 'Overcast')]
        db_questions = self.helper_create_db_questions(db_metar, questions_answers_text)
        mock_question_collector_db_question.side_effect = db_questions
        question_collector.generate_cloud_ceiling_questions()
        self.assertRaises(UsuableDataError)
        self.assertEquals(mock_question_collector_db_question.call_count, len(questions_answers_text))
        mock_question_collector_db_question.assert_has_calls([call(question_text, [answer_text]) for question_text, answer_text in questions_answers_text])
        for i in range(0, len(questions_answers_text)):
            self.assertEquals(question_collector.questions['cloud_{0}_ceiling_{1}'.format(questions_answers_text[i][1].lower(), i)], db_questions[i])


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_ceiling_question_cloud_units_empty(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'altitude'], ModifyJSONChoices.EMPTY)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_ceiling_questions()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(UsuableDataError)
        self.assertEquals(len(question_collector.questions), 0)


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_ceiling_question_cloud_type_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['clouds', 1, 'type'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        questions_answers_text = [('What kind of clouds have a ceiling of 2400 ft?', 'Few'),
                                  ('What kind of clouds have a ceiling of 4600 ft?', 'Overcast')]
        db_questions = self.helper_create_db_questions(db_metar, questions_answers_text)
        mock_question_collector_db_question.side_effect = db_questions
        question_collector.generate_cloud_ceiling_questions()
        self.assertRaises(KeyError)
        self.assertEquals(mock_question_collector_db_question.call_count, len(questions_answers_text))
        mock_question_collector_db_question.assert_has_calls([call(question_text, [answer_text]) for question_text, answer_text in questions_answers_text])
        for i in range(0, len(questions_answers_text)):
            self.assertEquals(question_collector.questions['cloud_{0}_ceiling_{1}'.format(questions_answers_text[i][1].lower(), i)], db_questions[i])


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_ceiling_question_cloud_altitude_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['clouds', 2, 'altitude'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        questions_answers_text = [('What kind of clouds have a ceiling of 2400 ft?', 'Few'),
                                  ('What kind of clouds have a ceiling of 3600 ft?', 'Broken')]
        db_questions = self.helper_create_db_questions(db_metar, questions_answers_text)
        mock_question_collector_db_question.side_effect = db_questions
        question_collector.generate_cloud_ceiling_questions()
        self.assertRaises(KeyError)
        self.assertEquals(mock_question_collector_db_question.call_count, len(questions_answers_text))
        mock_question_collector_db_question.assert_has_calls([call(question_text, [answer_text]) for question_text, answer_text in questions_answers_text])
        for i in range(0, len(questions_answers_text)):
            self.assertEquals(question_collector.questions['cloud_{0}_ceiling_{1}'.format(questions_answers_text[i][1].lower(), i)], db_questions[i])


    @mock.patch('metar_practice.question_collector.QuestionColllector.create_db_question')
    def test_generate_cloud_ceiling_question_cloud_units_does_not_exist(self, mock_question_collector_db_question):
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        db_metar = self.helper_create_modified_metar_object(metar_path, self.db_airport, ['units', 'altitude'], ModifyJSONChoices.DELETE)
        question_collector = QuestionColllector(db_metar, self.sample_count)
        db_question = self.helper_create_db_question(db_metar, 'This is a test question string', ['This is a test answer string'])
        mock_question_collector_db_question.return_value = db_question
        question_collector.generate_cloud_ceiling_questions()
        mock_question_collector_db_question.assert_not_called()
        self.assertRaises(KeyError)
        self.assertEquals(len(question_collector.questions), 0)


class TestGenerateQuestions(TestCase):

    def helper_create_db_question(self, db_metar, question_text, answers_text):
        db_answers = []
        for answer_text in answers_text:
            db_answer = Answer(text=answer_text)
            db_answer.save()
            db_answers.append(db_answer)
        db_question = Question(metar=db_metar,
                               text=question_text)
        db_question.save()
        [db_question.answers.add(db_answer) for db_answer in db_answers]
        return db_question


    def helper_create_db_questions(self, db_metar, questions_answers_text):
        db_questions = []
        for question_text, answer_text in questions_answers_text:
            db_answer = Answer(text=answer_text)
            db_answer.save()
            db_question = Question(metar=db_metar,
                                   text=question_text)
            db_question.save()
            db_question.answers.add(db_answer)
            db_questions.append(db_question)
        return db_questions


    def setUp(self):
        db_airport = Airport(name='John F Kennedy International Airport',
                             city='New York',
                             country='United States',
                             icao='KJFK',
                             latitude='40.63980103',
                             longitude='-73.77890015')
        db_airport.save()
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'question_collector', 'sample_metar.json')
        with open(metar_path) as f:
            metar_json = json.load(f)
        self.db_metar = Metar(metar_json=json.dumps(metar_json),
                              airport=db_airport)
        self.db_metar.save()
        cloud_conversion = {'FEW' : 'few',
                            'SCT' : 'scattered',
                            'BKN' : 'broken',
                            'OVC' : 'overcast'}
        self.questions = {}
        self.questions['airport'] = self.helper_create_db_question(self.db_metar, 'What is the airport ICAO?', ['KJFK'])
        self.questions['time'] = self.helper_create_db_question(self.db_metar, 'What is time was this METAR report made?', ['1551 ZULU'])
        self.questions['wind_direction'] = self.helper_create_db_question(self.db_metar, 'What is the wind direction?', ['350 degrees'])
        self.questions['wind_speed'] = self.helper_create_db_question(self.db_metar, 'What is the wind speed?', ['21 kt'])
        self.questions['wind_gust'] = self.helper_create_db_question(self.db_metar, 'What is the wind gusting to?', ['29 kt'])
        self.questions['altimeter'] = self.helper_create_db_question(self.db_metar, 'What is the altimeter?', ['29.66 inHg'])
        self.questions['temperature'] = self.helper_create_db_question(self.db_metar, 'What is the temperature?', ['10 C'])
        self.questions['dewpoint'] = self.helper_create_db_question(self.db_metar, 'What is the dewpoint?', ['7 C'])
        self.questions['visibility'] = self.helper_create_db_question(self.db_metar, 'What is the visibility?', ['10 sm'])
        self.questions['cloud_coverage'] = self.helper_create_db_question(self.db_metar, 'What is the reported cloud coverage?', ['Few Clouds', 'Broken Clouds', 'Overcast Clouds'])
        self.questions['cloud_few_heights'] = self.helper_create_db_question(self.db_metar, 'What is the height of the few clouds?', ['2400 ft'])
        self.questions['cloud_broken_heights'] = self.helper_create_db_question(self.db_metar, 'What is the height of the broken clouds?', ['3600 ft'])
        self.questions['cloud_overcast_heights'] = self.helper_create_db_question(self.db_metar, 'What is the height of the overcast clouds?', ['4600 ft'])
        self.questions['cloud_few_ceiling_0'] = self.helper_create_db_question(self.db_metar, 'What kind of clouds have a ceiling of 2400 ft?', ['Few'])
        self.questions['cloud_broken_ceiling_1'] = self.helper_create_db_question(self.db_metar, 'What kind of clouds have a ceiling of 3600 ft?', ['Scattered'])
        self.questions['cloud_overcast_ceiling_2'] = self.helper_create_db_question(self.db_metar, 'What kind of clouds have a ceiling of 4600 ft?', ['Overcast'])


    def add_questions(self, question_collector):
        question_collector.questions = self.questions


    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_ceiling_questions')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_height_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_coverage_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_visibility_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_dewpoint_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_temperature_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_altimeter_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_gust_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_speed_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_direction_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_time_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_airport_question')
    def test_generate_questions_no_lmit(self,
                                        mock_question_collector_generate_airport_question,
                                        mock_question_collector_generate_time_question,
                                        mock_question_collector_generate_wind_direction_question,
                                        mock_question_collector_generate_wind_speed_question,
                                        mock_question_collector_generate_wind_gust_question,
                                        mock_question_collector_generate_altimeter_question,
                                        mock_question_collector_generate_temperature_question,
                                        mock_question_collector_generate_dewpoint_question,
                                        mock_question_collector_generate_visibility_question,
                                        mock_question_collector_generate_cloud_coverage_question,
                                        mock_question_collector_generate_cloud_height_question,
                                        mock_question_collector_generate_cloud_ceiling_questions):
        mock_question_collector_generate_airport_question.return_value = None
        mock_question_collector_generate_time_question.return_value = None
        mock_question_collector_generate_wind_direction_question.return_value = None
        mock_question_collector_generate_wind_speed_question.return_value = None
        mock_question_collector_generate_wind_gust_question.return_value = None
        mock_question_collector_generate_altimeter_question.return_value = None
        mock_question_collector_generate_temperature_question.return_value = None
        mock_question_collector_generate_dewpoint_question.return_value = None
        mock_question_collector_generate_visibility_question.return_value = None
        mock_question_collector_generate_cloud_coverage_question.return_value = None
        mock_question_collector_generate_cloud_height_question.return_value = None
        mock_question_collector_generate_cloud_ceiling_questions.return_value = None
        sample_count = None
        question_collector = QuestionColllector(self.db_metar, sample_count)
        self.add_questions(question_collector)
        chosen_questions = question_collector.generate_questions()
        mock_question_collector_generate_airport_question.assert_called_once()
        mock_question_collector_generate_time_question.assert_called_once()
        mock_question_collector_generate_wind_direction_question.assert_called_once()
        mock_question_collector_generate_wind_speed_question.assert_called_once()
        mock_question_collector_generate_wind_gust_question.assert_called_once()
        mock_question_collector_generate_altimeter_question.assert_called_once()
        mock_question_collector_generate_temperature_question.assert_called_once()
        mock_question_collector_generate_dewpoint_question.assert_called_once()
        mock_question_collector_generate_visibility_question.assert_called_once()
        mock_question_collector_generate_cloud_coverage_question.assert_called_once()
        self.assertEquals(mock_question_collector_generate_cloud_height_question.call_count, 4)
        mock_question_collector_generate_cloud_ceiling_questions.assert_called_once()
        self.assertEquals(len(chosen_questions), len(self.questions))


    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_ceiling_questions')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_height_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_coverage_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_visibility_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_dewpoint_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_temperature_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_altimeter_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_gust_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_speed_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_direction_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_time_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_airport_question')
    def test_generate_questions_lmit(self,
                                        mock_question_collector_generate_airport_question,
                                        mock_question_collector_generate_time_question,
                                        mock_question_collector_generate_wind_direction_question,
                                        mock_question_collector_generate_wind_speed_question,
                                        mock_question_collector_generate_wind_gust_question,
                                        mock_question_collector_generate_altimeter_question,
                                        mock_question_collector_generate_temperature_question,
                                        mock_question_collector_generate_dewpoint_question,
                                        mock_question_collector_generate_visibility_question,
                                        mock_question_collector_generate_cloud_coverage_question,
                                        mock_question_collector_generate_cloud_height_question,
                                        mock_question_collector_generate_cloud_ceiling_questions):
        mock_question_collector_generate_airport_question.return_value = None
        mock_question_collector_generate_time_question.return_value = None
        mock_question_collector_generate_wind_direction_question.return_value = None
        mock_question_collector_generate_wind_speed_question.return_value = None
        mock_question_collector_generate_wind_gust_question.return_value = None
        mock_question_collector_generate_altimeter_question.return_value = None
        mock_question_collector_generate_temperature_question.return_value = None
        mock_question_collector_generate_dewpoint_question.return_value = None
        mock_question_collector_generate_visibility_question.return_value = None
        mock_question_collector_generate_cloud_coverage_question.return_value = None
        mock_question_collector_generate_cloud_height_question.return_value = None
        mock_question_collector_generate_cloud_ceiling_questions.return_value = None
        sample_count = len(self.questions)-4
        question_collector = QuestionColllector(self.db_metar, sample_count)
        self.add_questions(question_collector)
        chosen_questions = question_collector.generate_questions()
        mock_question_collector_generate_airport_question.assert_called_once()
        mock_question_collector_generate_time_question.assert_called_once()
        mock_question_collector_generate_wind_direction_question.assert_called_once()
        mock_question_collector_generate_wind_speed_question.assert_called_once()
        mock_question_collector_generate_wind_gust_question.assert_called_once()
        mock_question_collector_generate_altimeter_question.assert_called_once()
        mock_question_collector_generate_temperature_question.assert_called_once()
        mock_question_collector_generate_dewpoint_question.assert_called_once()
        mock_question_collector_generate_visibility_question.assert_called_once()
        mock_question_collector_generate_cloud_coverage_question.assert_called_once()
        self.assertEquals(mock_question_collector_generate_cloud_height_question.call_count, 4)
        mock_question_collector_generate_cloud_ceiling_questions.assert_called_once()
        self.assertEquals(len(chosen_questions), sample_count)
        found_count = 0
        for db_question in self.questions.values():
            if db_question in chosen_questions:
                found_count += 1
        self.assertEquals(len(chosen_questions), found_count)


    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_ceiling_questions')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_height_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_coverage_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_visibility_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_dewpoint_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_temperature_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_altimeter_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_gust_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_speed_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_direction_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_time_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_airport_question')
    def test_generate_questions_negative_sample_count(self,
                                                      mock_question_collector_generate_airport_question,
                                                      mock_question_collector_generate_time_question,
                                                      mock_question_collector_generate_wind_direction_question,
                                                      mock_question_collector_generate_wind_speed_question,
                                                      mock_question_collector_generate_wind_gust_question,
                                                      mock_question_collector_generate_altimeter_question,
                                                      mock_question_collector_generate_temperature_question,
                                                      mock_question_collector_generate_dewpoint_question,
                                                      mock_question_collector_generate_visibility_question,
                                                      mock_question_collector_generate_cloud_coverage_question,
                                                      mock_question_collector_generate_cloud_height_question,
                                                      mock_question_collector_generate_cloud_ceiling_questions):
        mock_question_collector_generate_airport_question.return_value = None
        mock_question_collector_generate_time_question.return_value = None
        mock_question_collector_generate_wind_direction_question.return_value = None
        mock_question_collector_generate_wind_speed_question.return_value = None
        mock_question_collector_generate_wind_gust_question.return_value = None
        mock_question_collector_generate_altimeter_question.return_value = None
        mock_question_collector_generate_temperature_question.return_value = None
        mock_question_collector_generate_dewpoint_question.return_value = None
        mock_question_collector_generate_visibility_question.return_value = None
        mock_question_collector_generate_cloud_coverage_question.return_value = None
        mock_question_collector_generate_cloud_height_question.return_value = None
        mock_question_collector_generate_cloud_ceiling_questions.return_value = None
        sample_count = -sys.maxsize - 1
        question_collector = QuestionColllector(self.db_metar, sample_count)
        self.add_questions(question_collector)
        chosen_questions = question_collector.generate_questions()
        self.assertEquals(len(chosen_questions), len(self.questions))
        mock_question_collector_generate_airport_question.assert_called_once()
        mock_question_collector_generate_time_question.assert_called_once()
        mock_question_collector_generate_wind_direction_question.assert_called_once()
        mock_question_collector_generate_wind_speed_question.assert_called_once()
        mock_question_collector_generate_wind_gust_question.assert_called_once()
        mock_question_collector_generate_altimeter_question.assert_called_once()
        mock_question_collector_generate_temperature_question.assert_called_once()
        mock_question_collector_generate_dewpoint_question.assert_called_once()
        mock_question_collector_generate_visibility_question.assert_called_once()
        mock_question_collector_generate_cloud_coverage_question.assert_called_once()
        self.assertEquals(mock_question_collector_generate_cloud_height_question.call_count, 4)
        mock_question_collector_generate_cloud_ceiling_questions.assert_called_once()


    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_ceiling_questions')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_height_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_coverage_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_visibility_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_dewpoint_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_temperature_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_altimeter_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_gust_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_speed_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_direction_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_time_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_airport_question')
    def test_generate_questions_zero_sample_count(self,
                                                  mock_question_collector_generate_airport_question,
                                                  mock_question_collector_generate_time_question,
                                                  mock_question_collector_generate_wind_direction_question,
                                                  mock_question_collector_generate_wind_speed_question,
                                                  mock_question_collector_generate_wind_gust_question,
                                                  mock_question_collector_generate_altimeter_question,
                                                  mock_question_collector_generate_temperature_question,
                                                  mock_question_collector_generate_dewpoint_question,
                                                  mock_question_collector_generate_visibility_question,
                                                  mock_question_collector_generate_cloud_coverage_question,
                                                  mock_question_collector_generate_cloud_height_question,
                                                  mock_question_collector_generate_cloud_ceiling_questions):
        mock_question_collector_generate_airport_question.return_value = None
        mock_question_collector_generate_time_question.return_value = None
        mock_question_collector_generate_wind_direction_question.return_value = None
        mock_question_collector_generate_wind_speed_question.return_value = None
        mock_question_collector_generate_wind_gust_question.return_value = None
        mock_question_collector_generate_altimeter_question.return_value = None
        mock_question_collector_generate_temperature_question.return_value = None
        mock_question_collector_generate_dewpoint_question.return_value = None
        mock_question_collector_generate_visibility_question.return_value = None
        mock_question_collector_generate_cloud_coverage_question.return_value = None
        mock_question_collector_generate_cloud_height_question.return_value = None
        mock_question_collector_generate_cloud_ceiling_questions.return_value = None
        sample_count = 0
        question_collector = QuestionColllector(self.db_metar, sample_count)
        self.add_questions(question_collector)
        chosen_questions = question_collector.generate_questions()
        mock_question_collector_generate_airport_question.assert_called_once()
        mock_question_collector_generate_time_question.assert_called_once()
        mock_question_collector_generate_wind_direction_question.assert_called_once()
        mock_question_collector_generate_wind_speed_question.assert_called_once()
        mock_question_collector_generate_wind_gust_question.assert_called_once()
        mock_question_collector_generate_altimeter_question.assert_called_once()
        mock_question_collector_generate_temperature_question.assert_called_once()
        mock_question_collector_generate_dewpoint_question.assert_called_once()
        mock_question_collector_generate_visibility_question.assert_called_once()
        mock_question_collector_generate_cloud_coverage_question.assert_called_once()
        self.assertEquals(mock_question_collector_generate_cloud_height_question.call_count, 4)
        mock_question_collector_generate_cloud_ceiling_questions.assert_called_once()
        self.assertEquals(len(chosen_questions), len(self.questions))


    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_ceiling_questions')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_height_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_coverage_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_visibility_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_dewpoint_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_temperature_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_altimeter_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_gust_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_speed_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_direction_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_time_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_airport_question')
    def test_generate_questions_below_sample_count(self,
                                                   mock_question_collector_generate_airport_question,
                                                   mock_question_collector_generate_time_question,
                                                   mock_question_collector_generate_wind_direction_question,
                                                   mock_question_collector_generate_wind_speed_question,
                                                   mock_question_collector_generate_wind_gust_question,
                                                   mock_question_collector_generate_altimeter_question,
                                                   mock_question_collector_generate_temperature_question,
                                                   mock_question_collector_generate_dewpoint_question,
                                                   mock_question_collector_generate_visibility_question,
                                                   mock_question_collector_generate_cloud_coverage_question,
                                                   mock_question_collector_generate_cloud_height_question,
                                                   mock_question_collector_generate_cloud_ceiling_questions):
        mock_question_collector_generate_airport_question.return_value = None
        mock_question_collector_generate_time_question.return_value = None
        mock_question_collector_generate_wind_direction_question.return_value = None
        mock_question_collector_generate_wind_speed_question.return_value = None
        mock_question_collector_generate_wind_gust_question.return_value = None
        mock_question_collector_generate_altimeter_question.return_value = None
        mock_question_collector_generate_temperature_question.return_value = None
        mock_question_collector_generate_dewpoint_question.return_value = None
        mock_question_collector_generate_visibility_question.return_value = None
        mock_question_collector_generate_cloud_coverage_question.return_value = None
        mock_question_collector_generate_cloud_height_question.return_value = None
        mock_question_collector_generate_cloud_ceiling_questions.return_value = None
        sample_count = len(self.questions)-1
        question_collector = QuestionColllector(self.db_metar, sample_count)
        self.add_questions(question_collector)
        chosen_questions = question_collector.generate_questions()
        mock_question_collector_generate_airport_question.assert_called_once()
        mock_question_collector_generate_time_question.assert_called_once()
        mock_question_collector_generate_wind_direction_question.assert_called_once()
        mock_question_collector_generate_wind_speed_question.assert_called_once()
        mock_question_collector_generate_wind_gust_question.assert_called_once()
        mock_question_collector_generate_altimeter_question.assert_called_once()
        mock_question_collector_generate_temperature_question.assert_called_once()
        mock_question_collector_generate_dewpoint_question.assert_called_once()
        mock_question_collector_generate_visibility_question.assert_called_once()
        mock_question_collector_generate_cloud_coverage_question.assert_called_once()
        self.assertEquals(mock_question_collector_generate_cloud_height_question.call_count, 4)
        mock_question_collector_generate_cloud_ceiling_questions.assert_called_once()
        self.assertEquals(len(chosen_questions), sample_count)


    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_ceiling_questions')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_height_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_coverage_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_visibility_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_dewpoint_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_temperature_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_altimeter_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_gust_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_speed_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_direction_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_time_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_airport_question')
    def test_generate_questions_equal_sample_count(self,
                                                   mock_question_collector_generate_airport_question,
                                                   mock_question_collector_generate_time_question,
                                                   mock_question_collector_generate_wind_direction_question,
                                                   mock_question_collector_generate_wind_speed_question,
                                                   mock_question_collector_generate_wind_gust_question,
                                                   mock_question_collector_generate_altimeter_question,
                                                   mock_question_collector_generate_temperature_question,
                                                   mock_question_collector_generate_dewpoint_question,
                                                   mock_question_collector_generate_visibility_question,
                                                   mock_question_collector_generate_cloud_coverage_question,
                                                   mock_question_collector_generate_cloud_height_question,
                                                   mock_question_collector_generate_cloud_ceiling_questions):
        mock_question_collector_generate_airport_question.return_value = None
        mock_question_collector_generate_time_question.return_value = None
        mock_question_collector_generate_wind_direction_question.return_value = None
        mock_question_collector_generate_wind_speed_question.return_value = None
        mock_question_collector_generate_wind_gust_question.return_value = None
        mock_question_collector_generate_altimeter_question.return_value = None
        mock_question_collector_generate_temperature_question.return_value = None
        mock_question_collector_generate_dewpoint_question.return_value = None
        mock_question_collector_generate_visibility_question.return_value = None
        mock_question_collector_generate_cloud_coverage_question.return_value = None
        mock_question_collector_generate_cloud_height_question.return_value = None
        mock_question_collector_generate_cloud_ceiling_questions.return_value = None
        sample_count = len(self.questions)
        question_collector = QuestionColllector(self.db_metar, sample_count)
        self.add_questions(question_collector)
        chosen_questions = question_collector.generate_questions()
        mock_question_collector_generate_airport_question.assert_called_once()
        mock_question_collector_generate_time_question.assert_called_once()
        mock_question_collector_generate_wind_direction_question.assert_called_once()
        mock_question_collector_generate_wind_speed_question.assert_called_once()
        mock_question_collector_generate_wind_gust_question.assert_called_once()
        mock_question_collector_generate_altimeter_question.assert_called_once()
        mock_question_collector_generate_temperature_question.assert_called_once()
        mock_question_collector_generate_dewpoint_question.assert_called_once()
        mock_question_collector_generate_visibility_question.assert_called_once()
        mock_question_collector_generate_cloud_coverage_question.assert_called_once()
        self.assertEquals(mock_question_collector_generate_cloud_height_question.call_count, 4)
        mock_question_collector_generate_cloud_ceiling_questions.assert_called_once()
        self.assertEquals(len(chosen_questions), sample_count)


    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_ceiling_questions')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_height_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_cloud_coverage_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_visibility_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_dewpoint_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_temperature_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_altimeter_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_gust_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_speed_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_wind_direction_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_time_question')
    @mock.patch('metar_practice.question_collector.QuestionColllector.generate_airport_question')
    def test_generate_questions_no_questions(self,
                                             mock_question_collector_generate_airport_question,
                                             mock_question_collector_generate_time_question,
                                             mock_question_collector_generate_wind_direction_question,
                                             mock_question_collector_generate_wind_speed_question,
                                             mock_question_collector_generate_wind_gust_question,
                                             mock_question_collector_generate_altimeter_question,
                                             mock_question_collector_generate_temperature_question,
                                             mock_question_collector_generate_dewpoint_question,
                                             mock_question_collector_generate_visibility_question,
                                             mock_question_collector_generate_cloud_coverage_question,
                                             mock_question_collector_generate_cloud_height_question,
                                             mock_question_collector_generate_cloud_ceiling_questions):
        mock_question_collector_generate_airport_question.return_value = None
        mock_question_collector_generate_time_question.return_value = None
        mock_question_collector_generate_wind_direction_question.return_value = None
        mock_question_collector_generate_wind_speed_question.return_value = None
        mock_question_collector_generate_wind_gust_question.return_value = None
        mock_question_collector_generate_altimeter_question.return_value = None
        mock_question_collector_generate_temperature_question.return_value = None
        mock_question_collector_generate_dewpoint_question.return_value = None
        mock_question_collector_generate_visibility_question.return_value = None
        mock_question_collector_generate_cloud_coverage_question.return_value = None
        mock_question_collector_generate_cloud_height_question.return_value = None
        mock_question_collector_generate_cloud_ceiling_questions.return_value = None
        sample_count = len(self.questions)
        question_collector = QuestionColllector(self.db_metar, len(self.questions))
        chosen_questions = question_collector.generate_questions()
        self.assertIsNone(chosen_questions)
        mock_question_collector_generate_airport_question.assert_called_once()
        mock_question_collector_generate_time_question.assert_called_once()
        mock_question_collector_generate_wind_direction_question.assert_called_once()
        mock_question_collector_generate_wind_speed_question.assert_called_once()
        mock_question_collector_generate_wind_gust_question.assert_called_once()
        mock_question_collector_generate_altimeter_question.assert_called_once()
        mock_question_collector_generate_temperature_question.assert_called_once()
        mock_question_collector_generate_dewpoint_question.assert_called_once()
        mock_question_collector_generate_visibility_question.assert_called_once()
        mock_question_collector_generate_cloud_coverage_question.assert_called_once()
        self.assertEquals(mock_question_collector_generate_cloud_height_question.call_count, 4)
        mock_question_collector_generate_cloud_ceiling_questions.assert_called_once()
