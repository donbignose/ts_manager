from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.html import format_html

from .forms import MatchGenerationForm, SegmentForm
from .models import (
    League,
    LeagueTable,
    Match,
    MatchDay,
    Player,
    Season,
    SeasonTeam,
    SegmentScore,
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
    show_change_link = True


class LeagueTableInline(admin.TabularInline):
    model = LeagueTable
    extra = 0
    readonly_fields = ["team", "played", "points", "goal_difference"]
    fields = [
        "team",
        "played",
        "wins",
        "draws",
        "losses",
        "points",
        "goals_for",
        "goals_against",
        "goal_difference",
    ]


class SegmentScoreInline(admin.TabularInline):
    model = SegmentScore
    form = SegmentForm
    extra = 0  # No extra blank segments
    min_num = 7  # Ensure at least 7 segments are shown (D1-D5 and S1-S2)
    max_num = 7
    readonly_fields = ["segment_type"]
    fields = [
        "segment_type",
        "home_score",
        "away_score",
        "home_players",
        "away_players",
    ]
    filter_horizontal = [
        "home_players",
        "away_players",
    ]


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
    inlines = [MatchInline, LeagueTableInline]


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "status",
    ]  # Columns shown in the match list view
    list_filter = [
        "status",
        "date",
        "home_team",
        "away_team",
    ]  # Filters for narrowing down results
    search_fields = ["home_team__name", "away_team__name"]  # Search by team name
    inlines = [SegmentScoreInline]  # Show segments inline on the match detail page


admin.site.register(Venue)
