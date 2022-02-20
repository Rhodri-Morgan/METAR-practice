from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import TemplateView

from metar_practice import urls as metar_practice_urls


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(metar_practice_urls)),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
]
