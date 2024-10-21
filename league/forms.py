from django import forms
from django.utils.timezone import now


class MatchGenerationForm(forms.Form):
    start_date = forms.DateField(
        label="Start Date", initial=now().date, widget=forms.SelectDateWidget
    )
    interval_days = forms.IntegerField(
        label="Interval between match days (in days)", initial=7, min_value=1
    )
