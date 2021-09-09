from django import forms

from .models import Report


class ReportForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea(attrs={'id' : 'description_text_area'}),
                                  label='Have I made an error? Please give a short explanation below:',
                                  help_text='Please note there is no need to give question specifics, relevant data will also be logged.',
                                  required=True)

    class Meta:
        model = Report
        fields = ['description']
