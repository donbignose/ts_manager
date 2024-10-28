import django_tables2 as tables
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html, escape
from .models import Player, Team, SegmentScore, LeagueTable


class PlayerTable(tables.Table):
    first_name = tables.Column(
        linkify=True,
        attrs={"a": {"class": "text-blue-500 hover:underline"}},
        verbose_name=_("First Name"),
    )
    last_name = tables.Column(
        verbose_name=_("Last Name"),
    )

    class Meta:
        model = Player
        template_name = "django_tables2/material_tailwind.html"
        fields = ("first_name", "last_name")


class TeamTable(tables.Table):
    name = tables.Column(
        linkify=True,
        attrs={"a": {"class": "text-blue-500 hover:underline"}},
        verbose_name=_("Team Name"),
    )
    venue = tables.Column(verbose_name=_("Venue"))

    class Meta:
        model = Team
        template_name = "django_tables2/material_tailwind.html"
        fields = ("name", "venue")


class SegmentTable(tables.Table):
    segment_type = tables.Column(verbose_name=_("Segment Type"), orderable=False)
    home_players = tables.Column(verbose_name=_("Home Players"), orderable=False)
    home_score = tables.Column(verbose_name=_("Home Score"), orderable=False)
    away_score = tables.Column(verbose_name=_("Away Score"), orderable=False)
    away_players = tables.Column(verbose_name=_("Away Players"), orderable=False)

    class Meta:
        model = SegmentScore
        template_name = "django_tables2/material_tailwind.html"
        fields = (
            "segment_type",
            "home_players",
            "home_score",
            "away_score",
            "away_players",
        )

    def render_home_players(self, record):
        return format_html(
            "<br>".join([escape(str(player)) for player in record.home_players.all()])
        )

    def render_away_players(self, record):
        return format_html(
            "<br>".join([escape(str(player)) for player in record.away_players.all()])
        )


class LeagueTableTable(tables.Table):
    position = tables.Column(verbose_name="#")
    team = tables.Column(
        linkify=True,
        attrs={"a": {"class": "hover:text-blue-500 hover:underline"}},
    )
    played = tables.Column(verbose_name="P")
    wins = tables.Column(verbose_name="W")
    draws = tables.Column(verbose_name="D")
    losses = tables.Column(verbose_name="L")
    goals_for = tables.Column(verbose_name="G")
    goal_difference = tables.Column(verbose_name="GD")
    points = tables.Column(verbose_name="Pts")

    class Meta:
        model = LeagueTable
        template_name = "django_tables2/material_tailwind.html"
        fields = (
            "position",
            "team",
            "played",
            "points",
            "wins",
            "draws",
            "losses",
            "goals_for",
            "goal_difference",
        )

    def render_goals_for(self, value, record):
        return f"{value}:{record.goals_against}"
