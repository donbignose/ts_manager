from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from league.filter import PlayerFilter
from .models import MatchDay, Player, Season, SeasonTeam, Team, Match


def home(request):
    return render(request, "league/home.html")


def team_list(request):
    teams = Team.objects.all()
    return render(request, "league/team_list.html", {"teams": teams})


def team_detail(request, team_id):
    season_teams = (
        SeasonTeam.objects.filter(team_id=team_id, season__active=True)
        .select_related("season", "team", "team__venue")
        .prefetch_related("players", "team__home_matches", "team__away_matches")
    )
    season = season_teams.first().season
    team = season_teams.first().team
    return render(
        request,
        "league/team_detail.html",
        {
            "team": team,
            "season_teams": season_teams,
            "matches": team.get_schedule(season),
        },
    )


def match_day_list(request, season_id):
    season = get_object_or_404(Season, pk=season_id)
    match_days = season.match_days.all()
    return render(
        request,
        "league/match_day_list.html",
        {"match_days": match_days, "season": season},
    )


def match_day_detail(request, match_day_id):
    match_day = get_object_or_404(MatchDay, pk=match_day_id)
    matches = match_day.matches.all()
    return render(
        request,
        "league/match_day_detail.html",
        {"match_day": match_day, "matches": matches},
    )


def match_detail(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    return render(request, "league/match_detail.html", {"match": match})


def active_league(request):
    season = (
        Season.objects.filter(active=True, league__type="regular")
        .prefetch_related("match_days", "match_days__matches")
        .first()
    )
    return render(request, "league/active_league.html", {"season": season})


def active_cup(request):
    season = Season.objects.filter(active=True, league__type="cup").first()
    return render(request, "league/active_league.html", {"season": season})


@login_required
def submit_score(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    if request.method == "POST":
        # Handle score submission here, ensure that only players from home or away teams can submit
        pass
    return render(request, "league/submit_score.html", {"match": match})


def league_table(request, season_id):
    season = get_object_or_404(Season, pk=season_id)
    table = season.league_table.all().order_by("-points")
    return render(
        request, "league/league_table.html", {"table": table, "season": season}
    )


def player_list(request):
    player_filter = PlayerFilter(request.GET, queryset=Player.objects.all())
    return render(request, "league/player_list.html", {"player_filter": player_filter})


def player_detail(request, player_id):
    player = get_object_or_404(Player, pk=player_id)
    return render(request, "league/player_detail.html", {"player": player})
