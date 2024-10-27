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
        home_players = cleaned_data.get("home_players")
        away_players = cleaned_data.get("away_players")
        segment_type = self.instance.segment_type
        match = self.instance.match

        self.validate_scores(home_score, away_score, segment_number)

        self.validate_player_count(segment_type, home_players, "home")
        self.validate_player_count(segment_type, away_players, "away")

        self.validate_player_participation(home_players, match, "home")
        self.validate_player_participation(away_players, match, "away")
        return cleaned_data

    def validate_scores(self, home_score, away_score, segment_number):
        """
        Validates that the scores do not exceed the maximum allowed score for the segment.
        """
        home_score = home_score or 0  # Default to 0 if not provided
        away_score = away_score or 0  # Default to 0 if not provided
        max_score = segment_number * SegmentScore.MAX_SCORE

        if home_score > max_score or away_score > max_score:
            raise forms.ValidationError(
                f"Score cannot exceed {max_score} for segment {segment_number}."
            )

    def validate_player_count(self, segment_type, players, team):
        """
        Validates that singles segments have exactly 1 player and doubles segments have exactly 2 players.
        """
        if segment_type.startswith("S") and players.count() > 1:
            raise forms.ValidationError(
                f"{team.capitalize()} team must have exactly 1 player for singles segment {segment_type}."
            )
        elif segment_type.startswith("D") and players.count() not in [0, 2]:
            raise forms.ValidationError(
                f"{team.capitalize()} team must have exactly 2 players for doubles segment {segment_type}."
            )

    def validate_player_participation(self, players, match, team_type):
        """
        Validates that players are not playing more than allowed in restricted segments.
        """
        for player in players.all():
            conflicting_segments = SegmentScore.objects.filter(
                match=match, **{f"{team_type}_players": player}
            ).exclude(
                pk=self.instance.pk
            )  # Exclude the current segment being validated

            # Track player participation in restricted groups
            participation_tracker = {
                "group1": set(),
                "group2": set(),
                "group3": set(),
            }

            for segment in conflicting_segments:
                if segment.segment_type in SegmentScore.SEGMENT_GROUPS["group1"]:
                    participation_tracker["group1"].add(segment.segment_type)
                elif segment.segment_type in SegmentScore.SEGMENT_GROUPS["group2"]:
                    participation_tracker["group2"].add(segment.segment_type)
                elif segment.segment_type in SegmentScore.SEGMENT_GROUPS["group3"]:
                    participation_tracker["group3"].add(segment.segment_type)

            # Add current segment type to the tracker
            if self.instance.segment_type in SegmentScore.SEGMENT_GROUPS["group1"]:
                participation_tracker["group1"].add(self.instance.segment_type)
            elif self.instance.segment_type in SegmentScore.SEGMENT_GROUPS["group2"]:
                participation_tracker["group2"].add(self.instance.segment_type)
            elif self.instance.segment_type in SegmentScore.SEGMENT_GROUPS["group3"]:
                participation_tracker["group3"].add(self.instance.segment_type)

            # Check if any player plays more than once in a restricted group
            for group, participation in participation_tracker.items():
                if len(participation) > 1:
                    raise forms.ValidationError(
                        f"Player {player} cannot participate in multiple segments of the same group ({', '.join(participation)})."
                    )


class SegmentLineupForm(SegmentForm):
    class Meta:
        model = SegmentScore
        fields = ["home_players", "away_players"]
        widgets = {
            "home_players": forms.CheckboxSelectMultiple,
            "away_players": forms.CheckboxSelectMultiple,
        }


class SegmentScoreForm(forms.ModelForm):
    class Meta:
        model = SegmentScore
        fields = ["home_score", "away_score"]

    def clean(self):
        cleaned_data = super().clean()
        home_score = cleaned_data.get("home_score")
        away_score = cleaned_data.get("away_score")
        segment_number = self.instance.segment_number

        if (home_score is None) != (away_score is None):  # XOR check for None
            raise forms.ValidationError(
                "Both home score and away score must be provided, or both left empty."
            )
        if home_score is not None and away_score is not None:
            max_score = segment_number * SegmentScore.MAX_SCORE
            if home_score > max_score or away_score > max_score:
                raise forms.ValidationError(
                    f"Score cannot exceed {max_score} for segment {segment_number}."
                )

        return cleaned_data
