from django.contrib import admin

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
@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ("__str__",)
    inlines = [SeasonTeamInline]  # Manage teams for the season through the inline


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
