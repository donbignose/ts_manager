from django.urls import path
from . import views

urlpatterns = [
    # Home page
    path("", views.home, name="home"),
    # Team URLs
    path("teams/", views.TeamListView.as_view(), name="team_list"),
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
    path("matches/<int:pk>/", views.MatchDetailView.as_view(), name="match_detail"),
    path("matches/<int:match_id>/start/", views.start_match, name="start_match"),
    # Submit score URL
    path(
        "matches/<int:match_id>/submit-score/",
        views.SubmitScoreView.as_view(),
        name="submit_score",
    ),
    path(
        "matches/<int:match_id>/submit-lineup/",
        views.SubmitLineupView.as_view(),
        name="submit_lineup",
    ),
    # League table URL
    path(
        "seasons/<int:season_id>/league-table/", views.league_table, name="league_table"
    ),
    path("active-league/", views.ActiveLeagueView.as_view(), name="active_league"),
    path("active-cup/", views.active_cup, name="active_cup"),
    # Player URLs
    path("players/", views.PlayerListView.as_view(), name="player_list"),
    path("players/<int:player_id>/", views.player_detail, name="player_detail"),
]
