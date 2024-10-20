from django.urls import path
from . import views

urlpatterns = [
    # Home page
    path("", views.home, name="home"),
    # Team URLs
    path("teams/", views.team_list, name="team_list"),
    path("teams/<int:team_id>/", views.team_detail, name="team_detail"),
    # Match day URLs
    path(
        "seasons/<int:season_id>/match-days/",
        views.match_day_list,
        name="match_day_list",
    ),
    path(
        "match-days/<int:match_day_id>/",
        views.match_day_detail,
        name="match_day_detail",
    ),
    # Submit score URL
    path(
        "matches/<int:match_id>/submit-score/", views.submit_score, name="submit_score"
    ),
    # League table URL
    path(
        "seasons/<int:season_id>/league-table/", views.league_table, name="league_table"
    ),
    # Season team detail (team's roster for the season)
    path(
        "seasons/<int:season_id>/teams/<int:team_id>/",
        views.season_team_detail,
        name="season_team_detail",
    ),
    path("active-league/", views.active_league, name="active_league"),
    path("active-cup/", views.active_cup, name="active_cup"),
    # Player URLs
    path("players/", views.player_list, name="player_list"),
    path("players/<int:player_id>/", views.player_detail, name="player_detail"),
]
