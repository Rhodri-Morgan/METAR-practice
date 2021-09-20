from django.test import TestCase
import mock

import os

from metar_practice.load_airports import LoadAirports

from metar_practice.models import Airport


class TestIsValid(TestCase):

    def setUp(self):
        self.load_airports = LoadAirports()
        self.row = {'Name' : 'Goroka Airport',
                    'City' : 'Goroka',
                    'Country' : 'Papua New Guinea',
                    'ICAO' : 'AYGA',
                    'Latitude' : '-6.081689835',
                    'Longitude' : '145.3919983'}


    def test_is_valid(self):
        self.assertTrue(self.load_airports.is_valid(self.row))


    def test_is_valid_name_none(self):
        self.row['Name'] = None
        self.assertFalse(self.load_airports.is_valid(self.row))


    def test_is_valid_city_none(self):
        self.row['City'] = None
        self.assertFalse(self.load_airports.is_valid(self.row))


    def test_is_valid_country_none(self):
        self.row['Country'] = None
        self.assertFalse(self.load_airports.is_valid(self.row))


    def test_is_valid_icao_none(self):
        self.row['ICAO'] = None
        self.assertFalse(self.load_airports.is_valid(self.row))


    def test_is_valid_latitude_none(self):
        self.row['Latitude'] = None
        self.assertFalse(self.load_airports.is_valid(self.row))


    def test_is_valid_longitude_none(self):
        self.row['Longitude'] = None
        self.assertFalse(self.load_airports.is_valid(self.row))


    def test_is_valid_all_none(self):
        self.row['Name'] = None
        self.row['City'] = None
        self.row['Country'] = None
        self.row['ICAO'] = None
        self.row['Latitude'] = None
        self.row['Longitude'] = None
        self.assertFalse(self.load_airports.is_valid(self.row))


    def test_is_valid_name_empty(self):
        self.row['Name'] = ''
        self.assertFalse(self.load_airports.is_valid(self.row))


    def test_is_valid_city_empty(self):
        self.row['City'] = ''
        self.assertFalse(self.load_airports.is_valid(self.row))


    def test_is_valid_country_empty(self):
        self.row['Country'] = ''
        self.assertFalse(self.load_airports.is_valid(self.row))


    def test_is_valid_icao_empty(self):
        self.row['ICAO'] = ''
        self.assertFalse(self.load_airports.is_valid(self.row))


    def test_is_valid_latitude_empty(self):
        self.row['Latitude'] = ''
        self.assertFalse(self.load_airports.is_valid(self.row))


    def test_is_valid_longitude_empty(self):
        self.row['Longitude'] = ''
        self.assertFalse(self.load_airports.is_valid(self.row))


    def test_is_valid_all_empty(self):
        self.row['Name'] = ''
        self.row['City'] = ''
        self.row['Country'] = ''
        self.row['ICAO'] = ''
        self.row['Latitude'] = ''
        self.row['Longitude'] = ''
        self.assertFalse(self.load_airports.is_valid(self.row))


    def test_is_valid_mix_none_empty(self):
        self.row['Name'] = None
        self.row['City'] = ''
        self.row['Country'] = None
        self.row['ICAO'] = ''
        self.row['Latitude'] = None
        self.row['Longitude'] = ''
        self.assertFalse(self.load_airports.is_valid(self.row))


class TestLoadAirports(TestCase):

    def assertContainsAirports(self):
        for icao in self.sample_airport_icaos:
            try:
                db_airport = Airport.objects.get(icao=icao)
            except KeyError:
                return False
        return True


    def setUp(self):
        self.load_airports = LoadAirports()
        self.fictional_airports = [{'Name' : 'Great Sphinx Airport',
                                    'City' : 'Giza',
                                    'Country' : 'Egypt',
                                    'ICAO' : 'PHIX',
                                    'Latitude' : '29.9753',
                                    'Longitude' : '31.1376'},
                                   {'Name' : 'Leaning Tower of Pisa Airport',
                                    'City' : 'Pisa',
                                    'Country' : 'Italy',
                                    'ICAO' : 'PISA',
                                    'Latitude' : '43.7230',
                                    'Longitude' : '10.3966'},
                                   {'Name' : 'Uluru Airport',
                                    'City' : 'Alice Springs',
                                    'Country' : 'Australia',
                                    'ICAO' : 'ULRU',
                                    'Latitude' : '-25.3444',
                                    'Longitude' : '131.0369'}]
        for airport in self.fictional_airports:
            db_airport = Airport(name=airport['Name'],
                                 city=airport['City'],
                                 country=airport['Country'],
                                 icao=airport['ICAO'],
                                 latitude=airport['Latitude'],
                                 longitude=airport['Longitude'])
            db_airport.save()
        self.sample_airport_icaos = ['YSSY', 'EGLL', 'KJFK', 'NZWN', 'RJAA']


    @mock.patch('metar_practice.load_airports.LoadAirports.is_valid', return_value=True)
    @mock.patch('metar_practice.load_airports.os')
    def test_load_airports(self, mock_os, mock_load_airports_is_valid):
        mock_os.path.join.return_value = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'load_airports', 'sample_airports.csv')
        mock_load_airports_is_valid.return_value = True
        self.load_airports.main()
        self.assertEquals(len(Airport.objects.all()), len(self.sample_airport_icaos))
        self.assertContainsAirports()


    @mock.patch('metar_practice.load_airports.LoadAirports.is_valid', return_value=True)
    @mock.patch('metar_practice.load_airports.os')
    def test_load_airports_duplicates(self, mock_os, mock_load_airports_is_valid):
        mock_os.path.join.return_value = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'load_airports', 'sample_airports_duplicates.csv')
        mock_load_airports_is_valid.return_value = True
        self.load_airports.main()
        self.assertEquals(len(Airport.objects.all()), len(self.sample_airport_icaos))
        self.assertContainsAirports()


    @mock.patch('metar_practice.load_airports.LoadAirports.is_valid', return_value=True)
    @mock.patch('metar_practice.load_airports.os')
    def test_load_airports_empty(self, mock_os, mock_load_airports_is_valid):
        mock_os.path.join.return_value = os.path.join(os.getcwd(), 'metar_practice', 'tests', 'static', 'load_airports', 'sample_airports_empty.csv')
        mock_load_airports_is_valid.return_value = True
        self.load_airports.main()
        self.assertEquals(len(Airport.objects.all()), 0)
