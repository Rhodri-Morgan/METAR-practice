import django
import json
import os
import datetime
import sys

sys.path.append('..')
os.environ['DJANGO_SETTINGS_MODULE'] = 'rhodrithomasmorgan.settings'
django.setup()

from django.db import connection


cursor = connection.cursor()
cursor.execute("vacuum;")
