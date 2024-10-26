import django_tables2 as tables
from django.utils.html import format_html, escape
from .models import Player, Team, SegmentScore


class PlayerTable(tables.Table):
    first_name = tables.Column(
        linkify=True, attrs={"a": {"class": "text-blue-500 hover:underline"}}
    )

    class Meta:
        model = Player
        template_name = "django_tables2/material_tailwind.html"
        fields = ("first_name", "last_name")


class TeamTable(tables.Table):
    name = tables.Column(
        linkify=True, attrs={"a": {"class": "text-blue-500 hover:underline"}}
    )

    class Meta:
        model = Team
        template_name = "django_tables2/material_tailwind.html"
        fields = ("name", "venue")


class SegmentTable(tables.Table):
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
