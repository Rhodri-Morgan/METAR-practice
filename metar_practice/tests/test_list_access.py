from django.test import TestCase

from metar_practice.templatetags.list_access import index

import sys


class TestListAccess(TestCase):

    def test_list_access(self):
        indexable = ['test_1', 'test_2', 'test_3']
        i = 0
        expected = 'test_1'
        self.assertEquals(index(indexable, i), expected)


    def test_list_access_complex(self):
        indexable = ['test_{0}'.format(count+1) for count in range(0, 100)]
        i = 23
        expected = 'test_24'
        self.assertEquals(index(indexable, i), expected)


    def test_list_access_nested_list(self):
        indexable_nested = ['test_nested_1', 'test_nested_2']
        indexable = [indexable_nested, 'test_2', 'test_3']
        i = 0
        self.assertEquals(index(indexable, i), indexable_nested)


    def test_list_access_invalid_index(self):
        indexable = ['test_1', 'test_2', 'test_3']
        i = 3
        try:
            index(indexable, i)
            self.fail()
        except IndexError:
            pass


    def test_list_access_negative_index(self):
        indexable = ['test_1', 'test_2', 'test_3']
        i = -sys.maxsize - 1
        try:
            index(indexable, i)
            self.fail()
        except IndexError:
            pass
