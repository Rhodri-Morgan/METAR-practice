import json
import requests
import os


x = requests.get('https://avwx.rest/api/metar/EGLL?options=&airport=true&reporting=true&format=json&onfail=cache',
                 headers={'Authorization':os.environ.get('METAR_KEY')})
print(x.text)

