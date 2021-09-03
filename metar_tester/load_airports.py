import django
import csv
import os
import sys

sys.path.append('..')
os.environ['DJANGO_SETTINGS_MODULE'] = 'rhodrithomasmorgan.settings'
django.setup()

from metar_tester.models import Airport


# Only accepting airports that have usuable data
def is_valid(row):
    return (row['Name'] is not None or row['Name'] == '') and \
           (row['City'] is not None or row['City'] == '') and \
           (row['Country'] is not None or row['Country'] == '') and \
           (row['ICAO'] is not None or row['ICAO'] == '') and \
           (row['Latitude'] is not None or row['Latitude'] == '') and \
           (row['Longitude'] is not None or row['Longitude'] == '')


# Deletes existing
Airport.objects.all().delete()

# Add data from CSV
data_path = os.path.join(os.path.split(os.getcwd())[0], 'static', 'csv', 'metar_tester', 'airports.csv')
first_line = True
airport_count = 0
with open(data_path, mode='r', encoding="utf8") as f:
    r = csv.DictReader(f)
    for row in r:
        if not first_line and is_valid(row):
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
        elif first_line:
            first_line = False
print('Added {0} unique airports.'.format(airport_count))
