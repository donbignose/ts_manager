from django import forms
from django.utils.timezone import now

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Div, Layout, Row, Submit

from league.models import SegmentScore, SeasonTeam


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


class SegmentForm(forms.ModelForm):
    class Meta:
        model = SegmentScore
        fields = [
            "home_players",
            "away_players",
            "home_score",
            "away_score",
        ]
        widgets = {
            "home_players": forms.CheckboxSelectMultiple,  # Example of customizing the widget
            "away_players": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super(SegmentForm, self).__init__(*args, **kwargs)

        try:
            match = self.instance.match

            # Filter home_players to only include players from the home team in the correct season
            season = match.match_day.season  # Get the season from the match_day
            home_team = match.home_team
            away_team = match.away_team

            # Filter home players
            home_season_team = SeasonTeam.objects.get(season=season, team=home_team)
            self.fields["home_players"].queryset = home_season_team.players.all()

            # Filter away players
            away_season_team = SeasonTeam.objects.get(season=season, team=away_team)
            self.fields["away_players"].queryset = away_season_team.players.all()
        except SegmentScore.match.RelatedObjectDoesNotExist:
            pass

    def clean(self):
        cleaned_data = super().clean()
        home_score = cleaned_data.get("home_score") or 0
        away_score = cleaned_data.get("away_score") or 0
        segment_number = self.instance.segment_number

        max_score = segment_number * SegmentScore.MAX_SCORE
        if home_score > max_score or away_score > max_score:
            raise forms.ValidationError(
                f"Score cannot exceed {max_score} for segment {segment_number}."
            )

        return cleaned_data


class SegmentLineupForm(forms.ModelForm):
    class Meta:
        model = SegmentScore
        fields = ["home_players", "away_players"]
        widgets = {
            "home_players": forms.CheckboxSelectMultiple,
            "away_players": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super(SegmentLineupForm, self).__init__(*args, **kwargs)

        try:
            match = self.instance.match
            season = match.match_day.season
            home_team = match.home_team
            away_team = match.away_team

            # Filter home players
            home_season_team = SeasonTeam.objects.get(season=season, team=home_team)
            self.fields["home_players"].queryset = home_season_team.players.all()

            # Filter away players
            away_season_team = SeasonTeam.objects.get(season=season, team=away_team)
            self.fields["away_players"].queryset = away_season_team.players.all()
        except SegmentScore.match.RelatedObjectDoesNotExist:
            pass


class SegmentScoreForm(forms.ModelForm):
    class Meta:
        model = SegmentScore
        fields = ["home_score", "away_score"]

    def clean(self):
        cleaned_data = super().clean()
        home_score = cleaned_data.get("home_score")
        away_score = cleaned_data.get("away_score")
        segment_number = self.instance.segment_number

        max_score = segment_number * SegmentScore.MAX_SCORE
        if home_score > max_score or away_score > max_score:
            raise forms.ValidationError(
                f"Score cannot exceed {max_score} for segment {segment_number}."
            )

        return cleaned_data
