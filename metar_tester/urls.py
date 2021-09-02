from django.urls import path

from . import views


urlpatterns = [
    path('METAR/test/', views.begin_test, name='begin_test'),
]
