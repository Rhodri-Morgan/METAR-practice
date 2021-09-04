import django
import json
import requests
import os
import sys
import random

sys.path.append('..')
os.environ['DJANGO_SETTINGS_MODULE'] = 'rhodrithomasmorgan.settings'
django.setup()

from metar_tester.models import Airport


class METAR_colllector:

    # Gets METAR data for given ICAO in a dict format
    def get_data(self, icao):
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
        return Airport.objects.order_by('?').first()


    # Generates a question for the user to attempt
    def generate_questions(self, icao, data):
        questions = {}

        if 'units' not in data:
            return None

        if 'station' in data:
            questions['airport'] = {'question' : 'What is the airport ICAO?',
                                    'answer' : [data['station']],
                                    'answer_units' : '',
                                    'choices': []}
        if 'time' in data:
            questions['time'] = {'question' : 'What is time was this METAR report made?',
                                 'answer' : [data['time']['repr'][2:-1]],
                                 'answer_units' : 'ZULU',
                                 'choices': []}
        if 'wind_direction' in data:
            questions['wind_direction'] = {'question' : 'What is the wind direction?',
                                           'answer' : [str(data['wind_direction']['value'])],
                                           'answer_units' : 'degrees',
                                           'choices': []}
        if 'wind_gust' in data:
            gust = None
            if data['wind_gust'] is not None:
                gust = str(data['wind_gust']['value'])
            else:
                gust = 0

            questions['wind_gust'] = {'question' : 'What is the wind gusting to?',
                                      'answer' : [gust],
                                      'answer_units' : data['units']['wind_speed'],
                                      'choices': []}
        if 'wind_speed' in data:
            questions['wind_speed'] = {'question' : 'What is the wind speed?',
                                       'answer' : [str(data['wind_speed']['value'])],
                                       'answer_units' : data['units']['wind_speed'],
                                       'choices': []}
        if 'altimiter' in data:
            questions['altimeter'] = {'question' : 'What is the altimiter?',
                                      'answer' : [str(data['altimeter']['value'])],
                                      'answer_units' : data['units']['altimeter'],
                                      'choices': []}
        if 'temperature' in data:
            questions['temperature'] = {'question' : 'What is the temperature?',
                                      'answer' : [str(data['temperature']['value'])],
                                      'answer_units' : data['units']['temperature'],
                                      'choices': []}
        if 'dewpoint' in data:
            questions['dewpoint'] = {'question' : 'What is the dewpoint?',
                                     'answer' : [str(data['dewpoint']['value'])],
                                     'answer_units' : data['units']['temperature'],
                                     'choices': []}
        if 'visability' in data:
            questions['dewpoint'] = {'question' : 'What is the visiability?',
                                     'answer' : [str(data['visibility']['value'])],
                                     'answer_units' : data['units']['visibility'],
                                     'choices': []}
        if 'clouds' in data:
            cloud_heights = {'few': [], 'scattered': [], 'broken': [], 'overcast': []}

            for item in data['clouds']:
                cloud_type = None
                if item['type'] == 'FEW':
                    cloud_heights['few'].append(str(item['altitude'])+'00')
                elif item['type'] == 'SCT':
                    cloud_heights['scattered'].append(str(item['altitude'])+'00')
                elif item['type'] == 'BKN':
                    cloud_heights['broken'].append(str(item['altitude'])+'00')
                elif item['type'] == 'OVC':
                    cloud_heights['overcast'].append(str(item['altitude'])+'00')

            questions['cloud_few'] = {'question' : 'What is the height of the few clouds?',
                                      'answer' : [cloud_heights['few']],
                                      'answer_units' : data['units']['altitude'],
                                      'choices': []}

            questions['cloud_scattered'] = {'question' : 'What is the height of the scattered clouds?',
                                            'answer' : [cloud_heights['scattered']],
                                            'answer_units' : data['units']['altitude'],
                                            'choices': []}

            questions['cloud_broken'] = {'question' : 'What is the height of the broken clouds?',
                                         'answer' : [cloud_heights['broken']],
                                         'answer_units' : data['units']['altitude'],
                                         'choices': []}

            questions['cloud_overcast'] = {'question' : 'What is the height of the overcast clouds?',
                                           'answer' : [cloud_heights['overcast']],
                                           'answer_units' : data['units']['altitude'],
                                           'choices': []}

            count = 0
            for key, value in cloud_heights.items():
                for height in value:
                    questions['cloud_{0}'.format(count)] = {'question' : 'What kind of clouds have a ceiling of {0} ft?'.format(height),
                                                            'answer' : [key.upper()],
                                                            'answer_units' : data['units']['altitude'],
                                                            'choices': [key.capitalize() for key in cloud_heights.keys()]}
                    count += 1

        if len(questions) >= 1:
            return questions
        else:
            return None


    def get_package(self):
        while True:
            icao = self.get_random_airport().icao
            status = None
            data = None
            questions = None

            if icao is not None:
                status, data = self.get_data(icao)
                if status == 503:
                    return status, icao, data, questions

            if data is not None:
                questions = self.generate_questions(icao, data)

            if questions is not None:
                return status, icao, data, questions
