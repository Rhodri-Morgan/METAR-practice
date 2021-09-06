import django
import json
import requests
import os
import sys

sys.path.append('..')
os.environ['DJANGO_SETTINGS_MODULE'] = 'rhodrithomasmorgan.settings'
django.setup()

from metar_tester.models import Airport
from django.forms.models import model_to_dict


class METAR_colllector:

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
            return None

        if 'station' in raw_metar:
            questions['airport'] = {'question' : 'What is the airport ICAO?',
                                    'answer' : [raw_metar['station']],
                                    'answer_units' : '',
                                    'choices': []}
        if 'time' in raw_metar:
            questions['time'] = {'question' : 'What is time was this METAR report made?',
                                 'answer' : [raw_metar['time']['repr'][2:-1]],
                                 'answer_units' : 'ZULU',
                                 'choices': []}
        if 'wind_direction' in raw_metar:
            questions['wind_direction'] = {'question' : 'What is the wind direction?',
                                           'answer' : [str(raw_metar['wind_direction']['value'])],
                                           'answer_units' : 'degrees',
                                           'choices': []}
        if 'wind_gust' in raw_metar:
            gust = None
            if raw_metar['wind_gust'] is not None:
                gust = str(raw_metar['wind_gust']['value'])
            else:
                gust = 0

            questions['wind_gust'] = {'question' : 'What is the wind gusting to?',
                                      'answer' : [gust],
                                      'answer_units' : raw_metar['units']['wind_speed'],
                                      'choices': []}
        if 'wind_speed' in raw_metar:
            questions['wind_speed'] = {'question' : 'What is the wind speed?',
                                       'answer' : [str(raw_metar['wind_speed']['value'])],
                                       'answer_units' : raw_metar['units']['wind_speed'],
                                       'choices': []}
        if 'altimiter' in raw_metar:
            questions['altimeter'] = {'question' : 'What is the altimiter?',
                                      'answer' : [str(raw_metar['altimeter']['value'])],
                                      'answer_units' : raw_metar['units']['altimeter'],
                                      'choices': []}
        if 'temperature' in raw_metar:
            questions['temperature'] = {'question' : 'What is the temperature?',
                                      'answer' : [str(raw_metar['temperature']['value'])],
                                      'answer_units' : raw_metar['units']['temperature'],
                                      'choices': []}
        if 'dewpoint' in raw_metar:
            questions['dewpoint'] = {'question' : 'What is the dewpoint?',
                                     'answer' : [str(raw_metar['dewpoint']['value'])],
                                     'answer_units' : raw_metar['units']['temperature'],
                                     'choices': []}
        if 'visability' in raw_metar:
            questions['dewpoint'] = {'question' : 'What is the visiability?',
                                     'answer' : [str(raw_metar['visibility']['value'])],
                                     'answer_units' : raw_metar['units']['visibility'],
                                     'choices': []}
        if 'clouds' in raw_metar:
            cloud_heights = {'few': [], 'scattered': [], 'broken': [], 'overcast': []}

            for item in raw_metar['clouds']:
                cloud_type = None
                if item['type'] == 'FEW':
                    cloud_heights['few'].append(str(item['altitude'])+'00')
                elif item['type'] == 'SCT':
                    cloud_heights['scattered'].append(str(item['altitude'])+'00')
                elif item['type'] == 'BKN':
                    cloud_heights['broken'].append(str(item['altitude'])+'00')
                elif item['type'] == 'OVC':
                    cloud_heights['overcast'].append(str(item['altitude'])+'00')

            questions['cloud_few_heights'] = {'question' : 'What is the height of the few clouds?',
                                              'answer' : [cloud_heights['few']],
                                              'answer_units' : raw_metar['units']['altitude'],
                                              'choices': []}

            questions['cloud_scattered_heights'] = {'question' : 'What is the height of the scattered clouds?',
                                                    'answer' : [cloud_heights['scattered']],
                                                    'answer_units' : raw_metar['units']['altitude'],
                                                    'choices': []}

            questions['cloud_broken_heights'] = {'question' : 'What is the height of the broken clouds?',
                                                 'answer' : [cloud_heights['broken']],
                                                 'answer_units' : raw_metar['units']['altitude'],
                                                 'choices': []}

            questions['cloud_overcast_heights'] = {'question' : 'What is the height of the overcast clouds?',
                                                   'answer' : [cloud_heights['overcast']],
                                                   'answer_units' : raw_metar['units']['altitude'],
                                                   'choices': []}

            count = 0
            for key, value in cloud_heights.items():
                for height in value:
                    questions['cloud_{0}_{1}'.format(key, count)] = {'question' : 'What kind of clouds have a ceiling of {0} ft?'.format(height),
                                                                     'answer' : [key.upper()],
                                                                     'answer_units' : raw_metar['units']['altitude'],
                                                                     'choices': [key.capitalize() for key in cloud_heights.keys()]}
                    count += 1

        if len(questions) >= 1:
            return questions
        else:
            return None


    def get_package(self):
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
