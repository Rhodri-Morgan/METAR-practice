import django
import json
import os
import datetime
import sys

sys.path.append('..')
os.environ['DJANGO_SETTINGS_MODULE'] = 'rhodrithomasmorgan.settings'
django.setup()

from metar_practice.models import Metar
from metar_practice.models import Question

from metar_practice.metar_collector import MetarCollector
from metar_practice.question_collector import QuestionCollector


hour_pull_count = 50
database_question_limit = 100000

def main():
    metar_collector = MetarCollector()
    time_now = datetime.datetime.utcnow()
    for i in range(0, hour_pull_count):
        db_airport = metar_collector.get_random_airport()
        status = None
        db_metar = None
        db_questions = None

        if db_airport is not None:
            status, db_metar = metar_collector.get_raw_metar(db_airport)

        if status == 200 and db_metar is not None:
            question_colllector = QuestionCollector(db_metar)
            question_colllector.generate_questions()
            print('\nSuccessfully pulled METAR data {0}/{1}\n'.format(i+1, hour_pull_count))

        if db_airport is None or status != 200 or db_metar is None:
            print('\Failed to pull METAR data {0}/{1}\n'.format(i+1, hour_pull_count))

    print('\nRemoving overflow of METAR data')
    db_answers = []
    print(database_question_limit)
    while Question.objects.count() > database_question_limit:
        db_metar = Metar.objects.order_by("?").first()
        db_questions = Question.objects.filter(metar=db_metar)
        for db_question in db_questions:
            for db_answer in db_question.answers.all():
                if db_answer not in db_answers:
                    db_answers.append(db_answer)
        db_metar.delete()

    for db_answer in db_answers:
        db_questions = Question.objects.filter(answers=db_answer)
        if len(db_questions) == 0:
            db_answer.delete()
    print('\nSuccessfully completed {0} METAR data pull\n'.format(time_now))


if __name__ == "__main__":
    main()
