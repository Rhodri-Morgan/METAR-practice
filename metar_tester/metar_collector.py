import django
import json
import requests
import os
import sys
from enum import Enum, auto


sys.path.append('..')
os.environ['DJANGO_SETTINGS_MODULE'] = 'rhodrithomasmorgan.settings'
django.setup()

from metar_tester.models import Airport
from django.forms.models import model_to_dict


# Encapsulation of question containing essential data/details
class Question:

    def __init__(self, text, answer, answer_units):
        self.text = text
        self.answer = answer
        self.answer_units = answer_units

    def is_trick(self):
        return len(self.answer) == 0


# Class for generating question sets and tasks associated with that task
class Question_Colllector:

    # Gets METAR data for given ICAO in a dict format
    def get_raw_metar(self, icao):
        url = 'https://avwx.rest/api/metar/{0}?options=&airport=true&reporting=true&format=json&onfail=cache'.format(icao)
        res = requests.get(url, headers={'Authorization':os.environ.get('METAR_KEY')})
        if res.status_code == 200:
            return res.status_code, json.loads(res.text)
        elif res.status_code == 400:
            Airport.objects.filter(icao=icao).delete()
            print('Removed airport {0}'.format(icao))
            return res.status_code, None
        else:
            return res.status_code, None


    # Gets a random airport from the database
    def get_random_airport(self):
        return model_to_dict(Airport.objects.order_by('?').first())


    # Generates a question for the user to attempt
    def generate_questions(self, raw_metar):
        questions = {}

        if 'units' not in raw_metar:
            return None                     # We need units to be specified to show quiz takers

        # STATION QUESTION
        if 'station' in raw_metar:
            questions['airport'] = Question('What is the airport ICAO?',
                                            [raw_metar['station']],
                                            '')
        # TIME QUESTION
        if 'time' in raw_metar:
            questions['time'] = Question('What is time was this METAR report made?',
                                         ['{0} {1}'.format(raw_metar['time']['repr'][2:-1], 'ZULU')],
                                         'ZULU')

        # WIND DIRECTION QUESTION
        questions['wind_direction'] = Question('What is the wind direction?',
                                               [],
                                               'degrees')
        if 'wind_direction' in raw_metar:
            questions['wind_direction'].answer.append('{0} {1}'.format(raw_metar['wind_direction']['value'], 'degrees'))

        # WIND GUST QUESTION
        questions['wind_gust'] = Question('What is the wind gusting to?',
                                          [],
                                          raw_metar['units']['wind_speed'])
        if 'wind_gust' in raw_metar:
            if raw_metar['wind_gust'] is not None:
                questions['wind_gust'].answer.append('{0} {1}'.format(raw_metar['wind_gust']['value'], raw_metar['units']['wind_speed']))

        # WIND SPEED QUESTION
        questions['wind_speed'] = Question('What is the wind speed?',
                                           [],
                                           raw_metar['units']['wind_speed'])
        if 'wind_speed' in raw_metar:
            questions['wind_speed'].answer.append('{0} {1}'.format(raw_metar['wind_speed']['value'], raw_metar['units']['wind_speed']))


        # ALTIMITER QUESTION
        if 'altimiter' in raw_metar:
            questions['altimeter'] = Question('What is the altimiter?',
                                              ['{0} {1}'.format(raw_metar['altimeter']['value'], raw_metar['units']['altimeter'])],
                                              raw_metar['units']['altimeter'])

        # TEMPERATURE QUESTION
        if 'temperature' in raw_metar:
            questions['temperature'] = Question('What is the temperature?',
                                                ['{0} {1}'.format(raw_metar['temperature']['value'], raw_metar['units']['temperature'])],
                                                raw_metar['units']['temperature'])

        # DEWPOINT QUESTION
        if 'dewpoint' in raw_metar:
            questions['dewpoint'] = Question('What is the dewpoint?',
                                             ['{0} {1}'.format(raw_metar['dewpoint']['value'], raw_metar['units']['temperature'])],
                                             raw_metar['units']['temperature'])

        # VISABILITY QUESTION
        if 'visibility' in raw_metar:
            questions['visibility'] = Question('What is the visiability?',
                                               ['{0} {1}'.format(raw_metar['visibility']['value'], raw_metar['units']['visibility'])],
                                               raw_metar['units']['visibility'])

        # CLOUDS QUESTIONS
        if 'clouds' in raw_metar:
            cloud_heights = {'few': [], 'scattered': [], 'broken': [], 'overcast': []}

            for item in raw_metar['clouds']:
                cloud_type = None
                if item['type'] == 'FEW':
                    cloud_heights['few'].append('{0}00 {1}'.format(item['altitude'], raw_metar['units']['altitude']))
                elif item['type'] == 'SCT':
                    cloud_heights['scattered'].append('{0}00 {1}'.format(item['altitude'], raw_metar['units']['altitude']))
                elif item['type'] == 'BKN':
                    cloud_heights['broken'].append('{0}00 {1}'.format(item['altitude'], raw_metar['units']['altitude']))
                elif item['type'] == 'OVC':
                    cloud_heights['overcast'].append('{0}00 {1}'.format(item['altitude'], raw_metar['units']['altitude']))

            questions['cloud_few_heights'] = Question('What is the height of the few clouds?',
                                                      cloud_heights['few'],
                                                      raw_metar['units']['altitude'])

            questions['cloud_scattered_heights'] = Question('What is the height of the scattered clouds?',
                                                            cloud_heights['scattered'],
                                                            raw_metar['units']['altitude'])

            questions['cloud_broken_heights'] = Question('What is the height of the broken clouds?',
                                                         cloud_heights['broken'],
                                                         raw_metar['units']['altitude'])

            questions['cloud_overcast_heights'] = Question('What is the height of the overcast clouds?',
                                                           cloud_heights['broken'],
                                                           raw_metar['units']['altitude'])

            count = 0
            choices = [key.capitalize() for key in cloud_heights.keys()]
            for key, value in cloud_heights.items():
                for height in value:
                    questions['cloud_{0}_{1}'.format(key, count)] =  Question('What kind of clouds have a ceiling of {0}?'.format(height),
                                                                              [key.capitalize()],
                                                                              raw_metar['units']['altitude'])
                    count += 1

        if len(questions) >= 1:
            return questions
        else:
            return None


    def get_questions(self):
        while True:
            airport = self.get_random_airport()
            status = None
            raw_metar = None
            questions = None

            if airport is not None:
                status, raw_metar = self.get_raw_metar(airport['icao'])
                if status == 503:
                    return status, airport, raw_metar, questions

            if raw_metar is not None:
                questions = self.generate_questions(raw_metar)

            if questions is not None:
                return status, airport, raw_metar, questions
