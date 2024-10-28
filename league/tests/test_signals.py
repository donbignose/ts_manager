import pytest
from django.db.models.signals import post_save
from league.models import League, Match, MatchDay, Team, Season

from league.signals import update_standings_on_match_update


@pytest.fixture
def partial_match_day_setup(db):
    post_save.disconnect(update_standings_on_match_update, sender=Match)
    league = League.objects.create(name="Test League")
    season = Season.objects.create(year=2023, league=league)
    team1 = Team.objects.create(name="Team 1")
    team2 = Team.objects.create(name="Team 2")
    team3 = Team.objects.create(name="Team 3")
    team4 = Team.objects.create(name="Team 4")

    match_day = MatchDay.objects.create(
        season=season, round_number=1, date="2023-01-01"
    )

    # Create matches with one not finished
    Match.objects.create(
        match_day=match_day,
        home_team=team1,
        away_team=team2,
        date=match_day.date,
        status=Match.Status.FINISHED,
    )
    Match.objects.create(
        match_day=match_day,
        home_team=team3,
        away_team=team4,
        date=match_day.date,
        status=Match.Status.IN_PROGRESS,
    )
    post_save.connect(update_standings_on_match_update, sender=Match)

    return match_day


def test_update_standings_signal_not_called_with_unfinished_matches(
    partial_match_day_setup, mocker
):
    match_day = partial_match_day_setup

    mock_update_standings = mocker.patch(
        "league.signals.update_standings_for_new_match_day"
    )

    for match in Match.objects.filter(match_day=match_day):
        post_save.send(sender=Match, instance=match, created=False)

    mock_update_standings.assert_not_called()


@pytest.fixture
def finished_match_day_setup(db):
    post_save.disconnect(update_standings_on_match_update, sender=Match)

    league = League.objects.create(name="Test League")
    season = Season.objects.create(year=2023, league=league)
    team1 = Team.objects.create(name="Team 1")
    team2 = Team.objects.create(name="Team 2")
    team3 = Team.objects.create(name="Team 3")
    team4 = Team.objects.create(name="Team 4")

    match_day = MatchDay.objects.create(
        season=season, round_number=1, date="2023-01-01"
    )

    # Create matches with FINISHED status
    Match.objects.create(
        match_day=match_day,
        home_team=team1,
        away_team=team2,
        date=match_day.date,
        status=Match.Status.FINISHED,
    )
    Match.objects.create(
        match_day=match_day,
        home_team=team3,
        away_team=team4,
        date=match_day.date,
        status=Match.Status.FINISHED,
    )
    post_save.connect(
        update_standings_on_match_update,
        sender=Match,
    )

    return match_day


def test_update_standings_signal_called(finished_match_day_setup, mocker):
    match_day = finished_match_day_setup

    mock_update_standings = mocker.patch(
        "league.signals.update_standings_for_new_match_day"
    )

    for match in Match.objects.filter(match_day=match_day):
        post_save.send(sender=Match, instance=match, created=False)

    assert mock_update_standings.call_count == 2
