from django import forms

from .models import Report


class ReportForm(forms.ModelForm):
    """ Form allowing users to state issues with questions """
    description = forms.CharField(widget=forms.Textarea(attrs={'id' : 'description_text_area'}),
                                  label='Have I made an error? Please give a short explanation below:',
                                  help_text='There is no need to give question specifics, relevant weather data will also be logged.',
                                  required=True)

    class Meta:
        model = Report
        fields = ['description']
