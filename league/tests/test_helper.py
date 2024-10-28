import pytest
from league.models import (
    League,
    LeagueTable,
    Match,
    MatchDay,
    SegmentScore,
    Team,
    Season,
)
from league.helper import update_standings_for_new_match_day
from league.signals import update_standings_on_match_update
from django.db.models.signals import post_save


@pytest.fixture
def league_setup(db):
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

    match1 = Match.objects.create(
        match_day=match_day,
        home_team=team1,
        away_team=team2,
        date=match_day.date,
        status=Match.Status.NOT_STARTED,
    )
    match2 = Match.objects.create(
        match_day=match_day,
        home_team=team3,
        away_team=team4,
        date=match_day.date,
        status=Match.Status.NOT_STARTED,
    )

    # Add segments for match1
    SegmentScore.objects.update_or_create(
        match=match1,
        segment_number=1,
        defaults={"home_score": 2, "away_score": 1, "segment_type": "D1"},
    )
    SegmentScore.objects.update_or_create(
        match=match1,
        segment_number=2,
        defaults={"home_score": 1, "away_score": 0, "segment_type": "S1"},
    )

    # Add segments for match2
    SegmentScore.objects.update_or_create(
        match=match2,
        segment_number=1,
        defaults={"home_score": 1, "away_score": 1, "segment_type": "D1"},
    )
    SegmentScore.objects.update_or_create(
        match=match2,
        segment_number=2,
        defaults={"home_score": 1, "away_score": 1, "segment_type": "S1"},
    )
    match1.status = Match.Status.FINISHED
    match2.status = Match.Status.FINISHED
    match1.save()
    match2.save()

    post_save.connect(update_standings_on_match_update, sender=Match)

    return {
        "season": season,
        "teams": [team1, team2, team3, team4],
        "match_day": match_day,
    }


def test_standings_calculation(league_setup):
    match_day = league_setup["match_day"]
    teams = league_setup["teams"]

    update_standings_for_new_match_day(match_day)

    standings = LeagueTable.objects.filter(match_day=match_day).order_by(
        "-points", "-goal_difference", "-goals_for"
    )

    # Assertions for Team 1's stats
    team1_standing = standings.get(team=teams[0])
    assert team1_standing.wins == 1
    assert team1_standing.draws == 0
    assert team1_standing.losses == 0
    assert team1_standing.goals_for == 3
    assert team1_standing.goals_against == 1
    assert team1_standing.points == 3

    # Assertions for Team 2's stats
    team2_standing = standings.get(team=teams[1])
    assert team2_standing.wins == 0
    assert team2_standing.draws == 0
    assert team2_standing.losses == 1
    assert team2_standing.goals_for == 1
    assert team2_standing.goals_against == 3
    assert team2_standing.points == 0

    # Assertions for Team 3's stats
    team3_standing = standings.get(team=teams[2])
    assert team3_standing.wins == 0
    assert team3_standing.draws == 1
    assert team3_standing.losses == 0
    assert team3_standing.goals_for == 2
    assert team3_standing.goals_against == 2
    assert team3_standing.points == 1


def test_position_calculation(league_setup):
    match_day = league_setup["match_day"]
    update_standings_for_new_match_day(match_day)

    standings = LeagueTable.objects.filter(match_day=match_day).order_by("position")
    teams = league_setup["teams"]

    assert standings[0].team == teams[0]  # Team 1 first
    assert standings[1].team == teams[2]  # Team 3 or Team 4 next
    assert standings[2].team == teams[3]
    assert standings[3].team == teams[1]  # Team 2 last


def test_new_standings_creation(league_setup):
    match_day = league_setup["match_day"]
    update_standings_for_new_match_day(match_day)

    standings_count = LeagueTable.objects.filter(match_day=match_day).count()
    assert standings_count == 4

    for team in league_setup["teams"]:
        assert LeagueTable.objects.filter(match_day=match_day, team=team).exists()
