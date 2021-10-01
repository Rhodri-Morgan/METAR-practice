from django.test import TestCase

from django.urls import reverse, resolve

from metar_practice.views import metar_practice


class TestUrls(TestCase):

    def test_metar_practice(self):
        url = reverse('metar_practice')
        self.assertEquals(resolve(url).func, metar_practice)
