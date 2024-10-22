import django_tables2 as tables
from .models import Player


class PlayerTable(tables.Table):
    class Meta:
        model = Player
        template_name = "django_tables2/material_tailwind.html"
        fields = ("first_name", "last_name")
