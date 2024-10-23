from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView
from django.views.generic.edit import FormView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from league.filter import PlayerFilter

from .forms import SegmentScoreForm, SegmentLineupForm
from .models import Match, MatchDay, Player, Season, SeasonTeam, SegmentScore, Team
from .tables import PlayerTable, TeamTable


def home(request):
    today = timezone.now().date()
    previous_match_day = (
        MatchDay.objects.filter(date__lte=today)
        .order_by("date")
        .prefetch_related("matches__home_team", "matches__away_team")
        .first()
    )

    next_match_day = (
        MatchDay.objects.filter(date__gt=today)
        .order_by("date")
        .prefetch_related("matches__home_team", "matches__away_team")
        .first()
    )

    context = {
        "previous_match_day": previous_match_day,
        "next_match_day": next_match_day,
    }

    return render(request, "league/home.html", context)


class TeamListView(SingleTableMixin, ListView):
    queryset = Team.objects.all().select_related("venue")
    table_class = TeamTable
    template_name = "league/team_list.html"
    paginate_by = 10


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


class SubmitView(FormView):
    template_name = None
    _form = None

    def get_form_class(self):
        # Use modelformset_factory to create a formset for SegmentScore
        return modelformset_factory(SegmentScore, form=self._form, extra=0)

    def get_match(self):
        return get_object_or_404(Match, id=self.kwargs["match_id"])

    def get_queryset(self):
        # Fetch all segment scores related to the match
        match = self.get_match()
        return SegmentScore.objects.filter(match=match).order_by("segment_number")

    def get_form_kwargs(self):
        """
        Pass additional data to the formset such as the queryset (the segments for the match).
        """
        kwargs = super().get_form_kwargs()
        kwargs["queryset"] = self.get_queryset()
        return kwargs

    def form_valid(self, formset):
        """
        Handle valid formset submission.
        """
        formset.save()  # Save all the forms in the formset
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        """
        Add match information to the template context.
        """
        context = super().get_context_data(**kwargs)
        context["match"] = self.get_match()
        return context

    def get_success_url(self):
        """
        Redirect to the match_detail page of the match.
        """
        match = self.get_match()
        return reverse("match_detail", kwargs={"match_id": match.id})


class SubmitScoreView(SubmitView):
    template_name = "league/submit_score.html"
    _form = SegmentScoreForm


class SubmitLineupView(SubmitView):
    template_name = "league/submit_lineup.html"
    _form = SegmentLineupForm


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


class PlayerListView(SingleTableMixin, FilterView):
    table_class = PlayerTable
    template_name = "league/player_list.html"
    filterset_class = PlayerFilter
    queryset = Player.objects.all()
    paginate_by = 10


def player_detail(request, player_id):
    player = get_object_or_404(Player, pk=player_id)
    return render(request, "league/player_detail.html", {"player": player})
