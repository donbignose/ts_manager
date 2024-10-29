from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Sum
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.http.response import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView, DetailView, TemplateView, View
from django.views.generic.edit import FormView
from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from league.filter import PlayerFilter

from .forms import SegmentScoreForm, SegmentLineupForm
from .models import (
    LeagueTable,
    Match,
    MatchDay,
    Player,
    Season,
    SeasonTeam,
    SegmentScore,
    Team,
)
from .tables import LeagueTableTable, PlayerTable, TeamTable, SegmentTable


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
    paginate_by = 10

    def get_template_names(self):
        if self.request.htmx:
            template_name = "league/partials/table.html"
        else:
            template_name = "league/team_list.html"

        return template_name


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


class MatchDetailView(SingleTableMixin, DetailView):
    model = Match
    table_class = SegmentTable
    template_name = "league/match_detail.html"

    def get_table_data(self):
        match = self.get_object()
        return match.segments.all()


class ActiveLeagueView(SingleTableMixin, TemplateView):
    table_class = LeagueTableTable

    def get_template_names(self):
        if self.request.htmx:
            template_name = "league/partials/table.html"
        else:
            template_name = "league/active_league.html"

        return template_name

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["season"] = (
            Season.objects.filter(active=True, league__type="regular")
            .prefetch_related(
                "match_days",
                Prefetch(
                    "match_days__matches",
                    queryset=Match.objects.annotate(
                        total_home_score=Sum("segments__home_score"),
                        total_away_score=Sum("segments__away_score"),
                    ).prefetch_related("home_team", "away_team"),
                ),
            )
            .first()
        )
        return context

    def get_table_data(self):
        active_league_table = (
            LeagueTable.objects.filter(
                match_day__season__active=True,
                match_day__season__league__type="regular",
            )
            .select_related("team", "match_day")
            .all()
        )
        return active_league_table


def active_cup(request):
    season = Season.objects.filter(active=True, league__type="cup").first()
    return render(request, "league/active_league.html", {"season": season})


class SubmitView(LoginRequiredMixin, FormView):
    template_name = None
    _form = None

    def dispatch(self, request, *args, **kwargs):
        """
        Perform authorization checks before handling the request.
        """
        team_role, team = self.get_team_and_role()

        if not team_role:
            return HttpResponseForbidden(
                "You are not authorized to submit for that match."
            )

        request.team_role = team_role
        request.team = team
        return super().dispatch(request, *args, **kwargs)

    def get_form_class(self):
        return modelformset_factory(SegmentScore, form=self._form, extra=0)

    def get_match(self):
        return get_object_or_404(Match, id=self.kwargs["match_id"])

    def get_team_and_role(self) -> tuple[str, Team] | tuple[None, None]:
        """
        Return the user's team for the current season by checking the Player model.
        """
        match = self.get_match()

        try:
            player = self.request.user.player
        except Player.DoesNotExist:
            return None, None

        season = match.match_day.season
        current_team = player.get_current_team(season)

        if current_team == match.home_team:
            return "home", current_team
        elif current_team == match.away_team:
            return "away", current_team
        else:
            return None, None

    def get_queryset(self):
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

    def form_invalid(self, formset):
        """
        Handle formset errors.
        """
        return self.render_to_response(self.get_context_data(formset=formset))

    def get_context_data(self, formset=None, **kwargs):
        """
        Add match information to the template context.
        """
        context = super().get_context_data(**kwargs)
        context["match"] = self.get_match()
        context["formset"] = formset or self.get_restricted_formset(
            self.request.team_role
        )
        context["team_role"] = self.request.team_role
        return context

    def get_success_url(self):
        """
        Redirect to the match_detail page of the match.
        """
        match = self.get_match()
        return reverse("match_detail", kwargs={"pk": match.id})

    def get_restricted_formset(self, team_role):
        """
        Creates a formset and restrict the fields for the opposing team.
        """
        formset = self.get_form_class()(queryset=self.get_queryset())
        return formset


class SubmitScoreView(SubmitView):
    template_name = "league/submit_score.html"
    _form = SegmentScoreForm


class SubmitLineupView(SubmitView):
    template_name = "league/submit_lineup.html"
    _form = SegmentLineupForm

    def get_restricted_formset(self, team_role):
        """
        Creates a formset and restrict the fields for the opposing team.
        """
        formset = self.get_form_class()(queryset=self.get_queryset())

        for form in formset:
            if team_role == "home":
                form.fields["away_players"].widget.attrs["disabled"] = True
            elif team_role == "away":
                form.fields["home_players"].widget.attrs["disabled"] = True

        return formset


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
    filterset_class = PlayerFilter
    queryset = Player.objects.all()
    paginate_by = 10

    def get_template_names(self):
        if self.request.htmx:
            template_name = "league/partials/table.html"
        else:
            template_name = "league/player_list.html"

        return template_name


def player_detail(request, player_id):
    player = get_object_or_404(Player, pk=player_id)
    return render(request, "league/player_detail.html", {"player": player})


@require_POST
def start_match(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    if match.status == Match.Status.NOT_STARTED:
        match.status = Match.Status.IN_PROGRESS
        match.save()
        return HttpResponse(Match.Status.IN_PROGRESS)
    return HttpResponse(status=400)
