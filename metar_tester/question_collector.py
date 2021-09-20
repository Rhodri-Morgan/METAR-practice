import django
import json
import os
import sys
import random

sys.path.append('..')
os.environ['DJANGO_SETTINGS_MODULE'] = 'rhodrithomasmorgan.settings'
django.setup()

from metar_tester.models import Answer
from metar_tester.models import Question


class UsuableDataError(Exception):
    pass


class QuestionColllector:

    def __init__(self, db_metar, sample_count):
        self.db_metar = db_metar
        self.metar = json.loads(db_metar.metar_json)
        if sample_count is not None and sample_count <= 0:
            self.sample_count = None
        else:
            self.sample_count = sample_count
        self.questions = {}


    def create_db_answers(self, answers):
        db_answers = []
        while len(answers) != 0:
            answer = answers.pop(0)
            db_answer = None
            try:
                db_answer = Answer.objects.get(text=answer)
            except Answer.DoesNotExist:
                db_answer = Answer(text=answer)
                db_answer.save()
            db_answers.append(db_answer)
        return db_answers


    def create_db_question(self, text, answers):
        db_answers = self.create_db_answers(answers)
        db_question = None
        try:
            db_question = Question.objects.get(metar=self.db_metar,
                                               text=text)
            # Note to self no need to check answers here the answers are directly a result of the metar and question/text
        except Question.DoesNotExist:
            db_question = Question(metar=self.db_metar,
                                   text=text)
            db_question.save()
            [db_question.answers.add(db_answer) for db_answer in db_answers]
        return db_question


    def generate_airport_question(self):
        try:
            if self.metar['station'] is None or self.metar['station'] == '':
                raise UsuableDataError(' Airport Question - Data is not unusable')

            self.questions['airport'] = self.create_db_question('What is the airport ICAO?',
                                                                [self.metar['station']])
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_time_question(self):
        try:
            if self.metar['time']['repr'] is None or self.metar['time']['repr'] == '':
                raise UsuableDataError('Time Question - Data is not unusable')

            self.questions['time'] = self.create_db_question('What is time was this METAR report made?',
                                                             ['{0} {1}'.format(self.metar['time']['repr'][2:-1], 'ZULU')])
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_wind_direction_question(self):
        try:
            if self.metar['wind_direction']['value'] is None:
                raise UsuableDataError('Wind Direction Question - Data is not unusable')

            self.questions['wind_direction'] = self.create_db_question('What is the wind direction?',
                                                                       ['{0} {1}'.format(self.metar['wind_direction']['value'], 'degrees')])
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_wind_speed_question(self):
        try:
            if self.metar['wind_speed']['value'] is None or self.metar['units']['wind_speed'] is None or self.metar['units']['wind_speed'] == '':
                raise UsuableDataError('Wind Speed Question - Data is not unusable')

            self.questions['wind_speed'] = self.create_db_question('What is the wind speed?',
                                                                   ['{0} {1}'.format(self.metar['wind_speed']['value'], self.metar['units']['wind_speed'])])
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_wind_gust_question(self):
        try:
            if self.metar['units']['wind_speed'] is None or self.metar['units']['wind_speed'] == '':
                raise UsuableDataError('Wind Gust Question - Data is not unusable')

            answers = []
            if self.metar['wind_gust'] is not None:
                answers.append('{0} {1}'.format(self.metar['wind_gust']['value'], self.metar['units']['wind_speed']))
            else:
                answers.append('The wind is not currently gusting.')
            self.questions['wind_gust'] = self.create_db_question('What is the wind gusting to?',
                                                                  answers)
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_altimeter_question(self):
        try:
            if self.metar['altimeter']['value'] is None or self.metar['units']['altimeter'] is None or self.metar['units']['altimeter'] == '':
                raise UsuableDataError('Altimeter Question - Data is not unusable')

            self.questions['altimeter'] = self.create_db_question('What is the altimeter?',
                                                                  ['{0} {1}'.format(self.metar['altimeter']['value'], self.metar['units']['altimeter'])])
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_temperature_question(self):
        try:
            if self.metar['temperature']['value'] is None or self.metar['units']['temperature'] is None or self.metar['units']['temperature'] == '':
                raise UsuableDataError('Temperature Question - Data is not unusable')

            self.questions['temperature'] = self.create_db_question('What is the temperature?',
                                                                    ['{0} {1}'.format(self.metar['temperature']['value'], self.metar['units']['temperature'])])
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_dewpoint_question(self):
        try:
            if self.metar['dewpoint']['value'] is None or self.metar['units']['temperature'] is None or self.metar['units']['temperature'] == '':
                raise UsuableDataError('Dewpoint Question - Data is not unusable')

            self.questions['dewpoint'] = self.create_db_question('What is the dewpoint?',
                                                                 ['{0} {1}'.format(self.metar['dewpoint']['value'], self.metar['units']['temperature'])])
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_visibility_question(self):
        try:
            if self.metar['visibility']['value'] is None or self.metar['units']['visibility'] is None or self.metar['units']['visibility'] == '':
                raise UsuableDataError('Visibility Question - Data is not unusable')

            self.questions['visibility'] = self.create_db_question('What is the visibility?',
                                                                   ['{0} {1}'.format(self.metar['visibility']['value'], self.metar['units']['visibility'])])
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_cloud_coverage_question(self):
        try:
            if self.metar['clouds'] is None or len(self.metar['clouds']) == 0:
                raise UsuableDataError('Cloud Coverage Question - Data is not unusable')

            answers = []
            conversion = {'SKC' : 'Sky Clear',
                          'NDC' : 'NIL Cloud Detected',
                          'CLR' : 'No Clouds Below 12,000 ft',
                          'NSC' : 'No Significant Cloud',
                          'FEW' : 'Few Clouds',
                          'SCT' : 'Scattered Clouds',
                          'BKN' : 'Broken Clouds',
                          'OVC' : 'Overcast Clouds',
                          'VV' : 'Vertical Visability Warning'}
            for item in self.metar['clouds']:
                if item['type'] == None or item['type'] == '':
                    raise UsuableDataError('Cloud Coverage Question - Data is not unusable')
                elif conversion[item['type']] not in answers:
                    answers.append(conversion[item['type']])
            self.questions['cloud_coverage'] = self.create_db_question('What is the reported cloud coverage?',
                                                                       answers)
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_cloud_height_question(self, cloud):
        try:
            if self.metar['clouds'] is None or len(self.metar['clouds']) == 0 or self.metar['units']['altitude'] is None or self.metar['units']['altitude'] == '':
                raise UsuableDataError('Cloud Height Question - Data is not unusable')

            heights = []
            for item in self.metar['clouds']:
                if item['type'] == None or item['type'] == '' or item['altitude'] is None:
                    raise UsuableDataError('Cloud Coverage Question - Data is not unusable')
                elif item['type'] == cloud:
                    heights.append(item['altitude'])
            if len(heights) > 0:
                conversion = {'FEW' : 'few',
                              'SCT' : 'scattered',
                              'BKN' : 'broken',
                              'OVC' : 'overcast'}
                answers = []
                for item in sorted(heights):
                    answers.append('{0}00 {1}'.format(item, self.metar['units']['altitude']))
                self.questions['cloud_{0}_heights'.format(conversion[cloud])] = self.create_db_question('What is the height of the {0} clouds?'.format(conversion[cloud]),
                                                                                                        answers)
                return heights
        except (KeyError, UsuableDataError) as e:
            print(e)


    def generate_cloud_ceiling_questions(self):
        try:
            if self.metar['clouds'] is None or len(self.metar['clouds']) == 0 or self.metar['units']['altitude'] is None or self.metar['units']['altitude'] == '':
                raise UsuableDataError('Cloud Ceiling Questions - Data is not unusable')
        except (KeyError, UsuableDataError) as e:
            print(e)
            return

        conversion = {'FEW' : 'few',
                      'SCT' : 'scattered',
                      'BKN' : 'broken',
                      'OVC' : 'overcast'}
        count = 0
        for item in self.metar['clouds']:
            try:
                if item['type'] is None or item['type'] == '' or item['altitude'] is None:
                    raise UsuableDataError('Cloud Ceiling Question - Data is not unusable')
                elif item['type'] in conversion.keys():
                    self.questions['cloud_{0}_ceiling_{1}'.format(conversion[item['type']], count)] = self.create_db_question('What kind of clouds have a ceiling of {0}00 {1}?'.format(item['altitude'], self.metar['units']['altitude']),
                                                                                                                  [conversion[item['type']].capitalize()])
                    count += 1
            except (KeyError, UsuableDataError) as f:
                print(f)


    def generate_questions(self):
        self.generate_airport_question()
        self.generate_time_question()
        self.generate_wind_direction_question()
        self.generate_wind_speed_question()
        self.generate_wind_gust_question()
        self.generate_altimeter_question()
        self.generate_temperature_question()
        self.generate_dewpoint_question()
        self.generate_visibility_question()
        self.generate_cloud_coverage_question()
        for cloud in ['FEW', 'SCT', 'OVC', 'BKN']:
            self.generate_cloud_height_question(cloud)
        self.generate_cloud_ceiling_questions()

        chosen_questions = []
        if self.sample_count is None or len(self.questions) <= self.sample_count:
            chosen_questions = list(self.questions.values())
        else:
            chosen_questions = random.sample(list(self.questions.values()), k=self.sample_count)

        if len(chosen_questions) >= 1:
            return chosen_questions
        else:
            return None
