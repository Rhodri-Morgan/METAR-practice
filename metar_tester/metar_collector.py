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


class MetarCollector:

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
