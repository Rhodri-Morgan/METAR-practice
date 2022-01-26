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

print('\nRemoving overflow of METAR data')
database_question_limit = 100000
db_answers = []
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
