from django.contrib import admin
from django.urls import path, include

from metar_tester import urls as metar_tester_urls


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(metar_tester_urls)),
]
