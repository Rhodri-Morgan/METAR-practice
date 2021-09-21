from django.test import TestCase

from metar_practice.forms import ReportForm


class TestReportForm(TestCase):

    def test_report_form_valid(self):
        description = 'This is a test form string.'
        form_data = {'description': description}
        form = ReportForm(data=form_data)
        self.assertTrue(form.is_valid())


    def test_report_form_invalid(self):
        form_data = {'description': None}
        form = ReportForm(data=form_data)
        self.assertFalse(form.is_valid())


    def test_report_form_fields(self):
        form = ReportForm()
        self.assertIn('description', form.fields)
        self.assertInHTML('<textarea name="description" cols="40" rows="10" id="description_text_area" required></textarea>', str(form))
        self.assertInHTML('<label for="description_text_area">Have I made an error? Please give a short explanation below:</label>', str(form))
        self.assertInHTML('<span class="helptext">There is no need to give question specifics, relevant weather data will also be logged.</span>', str(form))
