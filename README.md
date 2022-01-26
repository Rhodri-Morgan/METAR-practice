![Banner Image](documentation_sources/banner.png)

# METAR Practice Page

*See [BACKGROUND.MD](BACKGROUND.md) for example, motivation, data sources and methodology.*

## Python and Dependencies

### Python Version

This project is using `Python 3.6.0`.

### Dependencies
 
 The list of dependencies for this project can be found in `requirements.txt` and can be installed using `pip install -r requirements.txt`. To build a new `requirements.txt` delete the old version, navigate to directory and run `pip freeze > requirements.txt`.
 
 ## Running/Testing
 
 ### Running Site
 
 You can start running the site using `python manage.py runserver` which can then be viewed by visiting `127.0.0.1:8000`. With `DEBUG = True` in `rhodrithomasmorgan/settings.py` this will present the current urls available.
 
 To access the admin panel visit `127.0.0.1:8000/admin` and use the login credentials `username=test` and `password=password`. Alternatively you can create a super user using `python manage.py createsuperuser`.

`metar_practice/pull_metar_data.py` is a seperate script which should be ran in parallel for METAR data pulling. 

`metar_practice/load_airports.py` is a script for inserting all airports into the database. It is a requirement.

 
 ### Testing Site
 
 You can run the testing suite using `python manage.py test`. Resulting errors will be show.
