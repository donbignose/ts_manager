from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.utils.html import format_html

from .forms import MatchGenerationForm
from league.models import (
    League,
    Match,
    MatchDay,
    Player,
    Season,
    SeasonTeam,
    Team,
    Venue,
)

admin.site.register(League)


class SeasonTeamInline(admin.TabularInline):
    model = SeasonTeam
    extra = 1  # Number of empty forms displayed by default


# Inline for managing players within a SeasonTeam
class PlayerInline(admin.TabularInline):
    model = SeasonTeam.players.through  # Link to players through the SeasonTeam model
    extra = 1


class MatchInline(admin.TabularInline):
    model = Match
    extra = 1


# Season admin
def generate_matches_view(request, season_id):
    season = Season.objects.get(pk=season_id)

    if request.method == "POST":
        form = MatchGenerationForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data["start_date"]
            interval_days = form.cleaned_data["interval_days"]

            result_message = season.generate_matches(
                start_date, interval_days
            )  # Call the method on the season
            messages.success(request, result_message)

            return redirect(
                "admin:league_season_changelist"
            )  # Redirect to the season list
    else:
        form = MatchGenerationForm()

    return render(
        request, "admin/generate_matches.html", {"form": form, "season": season}
    )


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("__str__", "generate_matches_button")
    inlines = [SeasonTeamInline]  # Manage teams for the season through the inline

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:season_id>/generate-matches/",
                self.admin_site.admin_view(generate_matches_view),
                name="generate_matches",
            ),
        ]
        return custom_urls + urls

    # Button to trigger match generation
    def generate_matches_button(self, obj):
        return format_html(
            f'<a class="button" href="{obj.id}/generate-matches/">Generate Matches</a>'
        )

    generate_matches_button.short_description = "Generate Matches"
    generate_matches_button.allow_tags = True


# Team admin
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "manager")
    inlines = [SeasonTeamInline]  # Manage the seasons where the team is involved


# Player admin
@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name")
    inlines = [PlayerInline]  # Manage the teams and seasons a player is part of


# Register SeasonTeam separately if you want to manage it directly in admin
@admin.register(SeasonTeam)
class SeasonTeamAdmin(admin.ModelAdmin):
    list_display = ("team", "season")
    filter_horizontal = ("players",)


@admin.register(MatchDay)
class MatchDayAdmin(admin.ModelAdmin):
    list_display = ("__str__",)
    inlines = [MatchInline]


admin.site.register(Venue)
