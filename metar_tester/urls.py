from django.urls import path

from . import views


urlpatterns = [
    path('METAR/practice/', views.practice, name='practice'),
]
