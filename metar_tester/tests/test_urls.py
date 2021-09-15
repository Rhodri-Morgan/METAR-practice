import unittest

from django.urls import reverse, resolve

from metar_tester.views import practice


class TestUrls(unittest.TestCase):

    def test_practice(self):
        url = reverse('practice')
        self.assertEquals(resolve(url).func, practice)
