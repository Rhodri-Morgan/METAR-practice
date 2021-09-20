from django.contrib import admin
from django.urls import path, include

from metar_practice import urls as metar_practice_urls


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(metar_practice_urls)),
]
