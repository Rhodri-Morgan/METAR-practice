from django.urls import path

from . import views


urlpatterns = [
    path('METAR_practice/', views.metar_practice, name='metar_practice'),
]
