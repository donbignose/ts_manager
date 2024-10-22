from django import forms
from django.utils.timezone import now

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Div, Layout, Row, Submit


class MatchGenerationForm(forms.Form):
    start_date = forms.DateField(
        label="Start Date", initial=now().date, widget=forms.SelectDateWidget
    )
    interval_days = forms.IntegerField(
        label="Interval between match days (in days)", initial=7, min_value=1
    )


class PlayerFilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "GET"  # Use GET to preserve query params in URL
        self.helper.layout = Layout(
            Div(
                Div("name", css_class="w-auto max-w-sm min-w-[200px] relative"),
                css_class="w-full flex justify-end items-center mt-4",
            ),
        )
