import django
import csv
import os
import sys

sys.path.append('..')
os.environ['DJANGO_SETTINGS_MODULE'] = 'rhodrithomasmorgan.settings'
django.setup()

from metar_tester.models import Airport

class LoadAirports:

    def is_valid(self, row):
        return (row['Name'] is not None and row['Name'] != '') and \
               (row['City'] is not None and row['City'] != '') and \
               (row['Country'] is not None and row['Country'] != '') and \
               (row['ICAO'] is not None and row['ICAO'] != '') and \
               (row['Latitude'] is not None and row['Latitude'] != '') and \
               (row['Longitude'] is not None and row['Longitude'] != '')


    def main(self):
        Airport.objects.all().delete()
        # data_path = os.path.join(os.path.split(os.getcwd())[0], 'static', 'csv', 'metar_tester', 'airports.csv')
        data_path = os.path.join(os.getcwd(), 'metar_tester', 'tests', 'static', 'load_airports', 'sample_airports.csv')
        airport_count = 0
        with open(data_path, mode='r', encoding='utf8') as f:
            r = csv.DictReader(f)
            for row in r:
                if self.is_valid(row):
                    try:
                        db_airport = Airport.objects.get(icao=row['ICAO'])          # To avoid adding duplicates
                    except Airport.DoesNotExist:
                        db_airport = Airport(name=row['Name'],
                                            city=row['City'],
                                            country=row['Country'],
                                            icao=row['ICAO'],
                                            latitude=row['Latitude'],
                                            longitude=row['Longitude'])
                    db_airport.save()
                    airport_count += 1
        print('Added {0} unique airports.'.format(airport_count))


if __name__ == '__main__':
    load_airports = LoadAirports()
    load_airports.main()
