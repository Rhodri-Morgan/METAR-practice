import django
import json
import requests
import os
import datetime
import sys

sys.path.append('..')
os.environ['DJANGO_SETTINGS_MODULE'] = 'rhodrithomasmorgan.settings'
django.setup()

from metar_practice.metar_collector import MetarCollector
from metar_practice.question_collector import QuestionColllector


class PullMetarData:

    def __init__(self):
        self.metar_collector = MetarCollector()
        self.hour_pull_count = 10


    def main(self):
        next_pull = datetime.datetime.utcnow()
        while True:
            time_now = datetime.datetime.utcnow()
            if time_now >= next_pull:
                print('Beginning pulling {0} METAR data\n'.format(time_now))
                for i in range (0, self.hour_pull_count):
                    while True:
                        db_airport = self.metar_collector.get_random_airport()
                        db_metar = None
                        db_questions = None

                        if db_airport is not None:
                            status, db_metar = self.metar_collector.get_raw_metar(db_airport)

                        if db_metar is not None:
                            metar = json.loads(db_metar.metar_json)
                            question_colllector = QuestionColllector(db_metar)
                            db_questions = question_colllector.generate_questions()

                        if len(db_questions) != 0:
                            break
                    print('\nSuccessfully pulled {0}/{1}\n'.format(i+1, self.hour_pull_count))
                print('\nSuccessfully completed {0} METAR data pull\n'.format(time_now))
                next_pull = datetime.datetime.utcnow() + datetime.timedelta(hours=1)


if __name__ == '__main__':
    pull_metar_data = PullMetarData()
    pull_metar_data.main()
