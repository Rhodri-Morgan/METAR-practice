from django.urls import path

from . import views


urlpatterns = [
    path('METAR/practice/', views.open_practice, name='open_practice'),
]
