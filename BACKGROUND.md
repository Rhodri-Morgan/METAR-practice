![Banner Image](documentation_sources/banner.png)

# METAR Practice Page

Weather METeorological Aerodrome Reports or METAR is one of the most widely used formats for the recording and comprehension of weather observations worldwide. Although METAR comes from weather stations and other similar types of locations, weather METAR is most commonly reported at airports and is used by pilots in the planning and execution of flights everyday. With this in mind, my service takes METAR data from a collection of ~7000 airports from all over the world and prompts the user with simple questions regarding items specified in the report that they must be able to parse including air temperature, atmospheric pressure, wind speed and more. 

https://user-images.githubusercontent.com/52254823/136636728-5bcc1d2c-b61f-42e1-8dd8-1bd0562a044a.mp4

# Methodologies:

For this site to function there are two essential dependencies. Firstly, before running the site or pulling METAR data, airports must be extracted from the [ICAO dataset](https://www.kaggle.com/mike90/airport-codes) and added to the database. This will include information like airport name, ICAO, city, country, latitude and longitude. The second dependency is to have a flow of incoming METAR data. At hourly intervals utilising the [AVWX API](https://avwx.rest/#), the site will pull METAR data from a randomly selected database airport and generate as many questions for that METAR report as it feasibly can (we cannot generate a remarks question if this section is not defined in the METAR report). These questions are then stored in the database with corresponding answers. With these requirements fulfilled the site now operates under the flow of the user visits the site, the [django](https://www.djangoproject.com/) instance queries the database to get a random question, the system collects all the corresponding essential data for the chosen question such as airport and METAR data and then finally formats this into a HTML template for the user to interact with.

# Data Sources:

For a list of airports I am using [Michael's 'ICAO Airport Codes' dataset.](https://www.kaggle.com/mike90/airport-codes)

For METAR data I am using [AVWX Aviation Weather REST API by Michael duPont.](https://avwx.rest/#)

Map of the location of airports is provided by [Google Maps Platform.](https://cloud.google.com/maps-platform)

# Status:

TODO
