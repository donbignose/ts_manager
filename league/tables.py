import django_tables2 as tables
from .models import Player, Team


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
