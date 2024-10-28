from .models import LeagueTable, Match


def update_standings_for_new_match_day(current_match_day):
    previous_standings_queryset = LeagueTable.objects.get_previous_standings(
        current_match_day
    )
    matches = Match.objects.filter(
        match_day=current_match_day, status=Match.Status.FINISHED
    )
    update_standings_from_matches(
        matches, previous_standings_queryset, current_match_day
    )
    set_team_positions(current_match_day)


def update_standings_from_matches(matches, standings_queryset, current_match_day):
    """
    Update standings based on the matches of the current match day.
    """
    for match in matches:
        home_team_standing = standings_queryset.filter(
            team=match.home_team
        ).first() or LeagueTable(team=match.home_team)
        away_team_standing = standings_queryset.filter(
            team=match.away_team
        ).first() or LeagueTable(team=match.away_team)

        home_team_standing.pk = None
        away_team_standing.pk = None

        home_team_standing.match_day = current_match_day
        away_team_standing.match_day = current_match_day

        increment_team_stats(home_team_standing, match.home_score, match.away_score)
        increment_team_stats(away_team_standing, match.away_score, match.home_score)

        home_team_standing.save()
        away_team_standing.save()


def increment_team_stats(team_standing, goals_for, goals_against):
    """
    Increment basic team stats: games played, goals for, and goals against.
    """
    team_standing.played += 1
    team_standing.goals_for += goals_for
    team_standing.goals_against += goals_against

    if goals_for > goals_against:
        team_standing.wins += 1
    elif goals_for < goals_against:
        team_standing.losses += 1
    else:
        team_standing.draws += 1


def set_team_positions(match_day):
    """
    Set the position of each team in the standings for the specified match day.
    """
    sorted_standings = LeagueTable.objects.filter(match_day=match_day).order_by(
        "-points", "-goal_difference", "-goals_for"
    )
    for position, standing in enumerate(sorted_standings, start=1):
        standing.position = position
        standing.save()
