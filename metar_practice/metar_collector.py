import django
import json
import requests
import os
import sys

sys.path.append('..')
os.environ['DJANGO_SETTINGS_MODULE'] = 'rhodrithomasmorgan.settings'
django.setup()

from metar_practice.models import Airport
from metar_practice.models import Metar
from django.forms.models import model_to_dict


class MetarCollector:

    def get_raw_metar(self, db_airport):
        """  Retrieves METAR report and creates corresponding Metar database object """
        try:
            icao = db_airport.icao
            url = 'https://avwx.rest/api/metar/{0}?options=&airport=true&reporting=true&format=json&onfail=cache'.format(icao)
            res = requests.get(url, headers={'Authorization':os.environ.get('METAR_KEY')})
            if res.status_code == 200:
                db_metar = None
                try:
                    db_metar = Metar.objects.get(metar_json=res.text,
                                                 airport=db_airport)          # To avoid adding duplicates
                except Metar.DoesNotExist:
                    db_metar = Metar(metar_json=res.text,
                                     airport=db_airport)
                    db_metar.full_clean()
                    db_metar.save()
                return res.status_code, db_metar
            else:
                if res.status_code == 400 and json.loads(res.text)['error'] == '{0} is not a valid ICAO or IATA code'.format(icao):
                    Airport.objects.filter(icao=icao).delete()
                return res.status_code, None
        except Exception as e:
            return None, None


    def get_random_airport(self):
        """  Retrieves random airport object """
        return Airport.objects.order_by('?').first()
