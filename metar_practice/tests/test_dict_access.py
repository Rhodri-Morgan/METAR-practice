from django.test import TestCase

from metar_practice.templatetags.dict_access import lookup


class TestDictAccess(TestCase):

    def test_dict_access(self):
        d = {'test_key' : 'test_value'}
        key = 'test_key'
        expected = 'test_value'
        self.assertEquals(lookup(d, key), expected)


    def test_dict_access_complex(self):
        d = {}
        for count in range(0, 100):
            d['test_key_{0}'.format(count)] = 'test_value_{0}'.format(count + 1)
        key = 'test_key_55'
        expected = 'test_value_56'
        self.assertEquals(lookup(d, key), expected)


    def test_dict_access_nested_dict(self):
        d_nested = {'another_test_key' : 'test_value'}
        d = {'test_key' : d_nested}
        key = 'test_key'
        self.assertEquals(lookup(d, key), d_nested)


    def test_dict_access_invalid_key(self):
        d = {'test_key' : 'test_value'}
        key = 'non_key'
        self.assertIsNone(lookup(d, key))
