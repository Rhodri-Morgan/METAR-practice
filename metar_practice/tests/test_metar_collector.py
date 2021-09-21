from django.test import TestCase
import responses

import os
import json

from metar_practice.metar_collector import MetarCollector
from metar_practice.question_collector import QuestionColllector

from metar_practice.models import Airport
from metar_practice.models import Metar


class TestGetRawMetar(TestCase):

    def helper_extract_json(self, path):
        extracted_json = None
        with open(path) as f:
            extracted_json = json.load(f)
        return json.dumps(extracted_json)


    def helper_get_db_airport(self, pk):
        db_airport = None
        try:
            db_airport = Airport.objects.get(pk=pk)
        except Airport.DoesNotExist:
            pass
        return db_airport


    @responses.activate
    def test_get_raw_metar_airport_exists(self):
        metar_collector = MetarCollector()
        icao = 'KJFK'
        db_airport = Airport(name='John F Kennedy International Airport',
                             city='New York',
                             country='United States',
                             icao=icao,
                             latitude='40.63980103',
                             longitude='-73.77890015')
        db_airport.full_clean()
        db_airport.save()
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'metar_collector', 'sample_metar.json')
        metar_json = self.helper_extract_json(metar_path)
        responses.add(method='GET',
                      url='https://avwx.rest/api/metar/{0}?options=&airport=true&reporting=true&format=json&onfail=cache'.format(icao),
                      body=metar_json,
                      status=200)
        status_code, returned_db_metar = metar_collector.get_raw_metar(db_airport)
        db_metar = None
        try:
            db_metar = Metar.objects.get(metar_json=metar_json,
                                         airport=db_airport)
        except Metar.DoesNotExist:
            self.fail('METAR not found')
        self.assertEquals(status_code, 200)
        self.assertEquals(returned_db_metar, db_metar)


    @responses.activate
    def test_get_raw_metar_airport_already_exists(self):
        metar_collector = MetarCollector()
        icao = 'KJFK'
        db_airport = Airport(name='John F Kennedy International Airport',
                             city='New York',
                             country='United States',
                             icao=icao,
                             latitude='40.63980103',
                             longitude='-73.77890015')
        db_airport.full_clean()
        db_airport.save()
        metar_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'metar_collector', 'sample_metar.json')
        metar_json = self.helper_extract_json(metar_path)
        db_metar = Metar(metar_json=metar_json,
                         airport=db_airport)
        db_airport.full_clean()
        db_metar.save()
        responses.add(method='GET',
                      url='https://avwx.rest/api/metar/{0}?options=&airport=true&reporting=true&format=json&onfail=cache'.format(icao),
                      body=metar_json,
                      status=200)
        status_code, returned_db_metar = metar_collector.get_raw_metar(db_airport)
        self.assertEquals(status_code, 200)
        self.assertEquals(returned_db_metar, db_metar)
        self.assertIsNotNone(self.helper_get_db_airport(db_airport.pk))


    @responses.activate
    def test_get_raw_metar_airport_error_airport_does_not_exist(self):
        metar_collector = MetarCollector()
        icao = 'AAAA'
        db_airport = Airport(name='Emerald Airport',
                             city='Emerald City',
                             country='Land of Oz',
                             icao=icao,
                             latitude='-18.42533',
                             longitude='58.38974')
        db_airport.full_clean()
        db_airport.save()
        error_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'metar_collector', 'sample_metar_error.json')
        error_json = self.helper_extract_json(error_path)
        responses.add(method='GET',
                      url='https://avwx.rest/api/metar/{0}?options=&airport=true&reporting=true&format=json&onfail=cache'.format(icao),
                      body=error_json,
                      status=400)
        status_code, returned_db_metar = metar_collector.get_raw_metar(db_airport)
        self.assertEquals(status_code, 400)
        self.assertEquals(returned_db_metar, None)
        self.assertIsNone(self.helper_get_db_airport(db_airport.pk))


    @responses.activate
    def test_get_raw_metar_airport_error_airport_does_not_exist_wrong_status_code(self):
        metar_collector = MetarCollector()
        icao = 'AAAA'
        db_airport = Airport(name='Emerald Airport',
                             city='Emerald City',
                             country='Land of Oz',
                             icao=icao,
                             latitude='-18.42533',
                             longitude='58.38974')
        db_airport.full_clean()
        db_airport.save()
        error_path = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'metar_collector', 'sample_metar_error.json')
        error_json = self.helper_extract_json(error_path)
        responses.add(method='GET',
                      url='https://avwx.rest/api/metar/{0}?options=&airport=true&reporting=true&format=json&onfail=cache'.format(icao),
                      body=error_json,
                      status=000)
        status_code, returned_db_metar = metar_collector.get_raw_metar(db_airport)
        self.assertEquals(status_code, 000)
        self.assertEquals(returned_db_metar, None)
        self.assertIsNotNone(self.helper_get_db_airport(db_airport.pk))


    @responses.activate
    def test_get_raw_metar_airport_error_exception(self):
        metar_collector = MetarCollector()
        icao = 'AAAA'
        db_airport = Airport(name='Emerald Airport',
                             city='Emerald City',
                             country='Land of Oz',
                             icao=icao,
                             latitude='-18.42533',
                             longitude='58.38974')
        db_airport.full_clean()
        db_airport.save()
        status_code, returned_db_metar = metar_collector.get_raw_metar(db_airport)
        self.assertRaises(Exception)
        self.assertEquals(status_code, None)
        self.assertEquals(returned_db_metar, None)
        self.assertIsNotNone(self.helper_get_db_airport(db_airport.pk))


class TestGetRandomAirport(TestCase):

    def test_get_random_airport(self):
        metar_collector = MetarCollector()
        db_airport = Airport(name='John F Kennedy International Airport',
                             city='New York',
                             country='United States',
                             icao='KJFK',
                             latitude='40.63980103',
                             longitude='-73.77890015')
        db_airport.full_clean()
        db_airport.save()
        returned_db_airport = metar_collector.get_random_airport()
        self.assertEqual(returned_db_airport, db_airport)


    def test_get_random_airport_empty(self):
        metar_collector = MetarCollector()
        returned_db_airport = metar_collector.get_random_airport()
        self.assertIsNone(returned_db_airport)
