import django
import json
import os
import datetime
import sys

sys.path.append('..')
os.environ['DJANGO_SETTINGS_MODULE'] = 'rhodrithomasmorgan.settings'
django.setup()

from metar_practice.metar_collector import MetarCollector
from metar_practice.question_collector import QuestionCollector


hour_pull_count = 50
metar_collector = MetarCollector()
time_now = datetime.datetime.utcnow()
for i in range (0, hour_pull_count):
    while True:
        db_airport = metar_collector.get_random_airport()
        db_metar = None
        db_questions = None

        if db_airport is not None:
            status, db_metar = metar_collector.get_raw_metar(db_airport)

        if db_metar is not None:
            metar = json.loads(db_metar.metar_json)
            question_colllector = QuestionCollector(db_metar)
            db_questions = question_colllector.generate_questions()

        if status == 429 or (db_questions is not None and len(db_questions) != 0):
            break
    print('\nSuccessfully pulled {0}/{1}\n'.format(i+1, hour_pull_count))
print('\nSuccessfully completed {0} METAR data pull\n'.format(time_now))
