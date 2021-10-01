from django.urls import path

from . import views


urlpatterns = [
    path('METAR_practice/', views.METAR_practice, name='METAR_practice'),
]
