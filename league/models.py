import random
from django.core.exceptions import ValidationError
from datetime import timedelta
from itertools import combinations
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class League(models.Model):
    LEAGUE_TYPE_CHOICES = [
        ("regular", "Regular League"),
        ("cup", "Cup"),
    ]
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=LEAGUE_TYPE_CHOICES)

    def __str__(self):
        return self.name


class Venue(models.Model):
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    address = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Season(models.Model):
    year = models.IntegerField()
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    active = models.BooleanField(default=False)
    teams = models.ManyToManyField("Team", through="SeasonTeam", related_name="seasons")

    def __str__(self):
        return f"{self.league} {self.year}/{self.year + 1}"

    def generate_matches(self, start_date, interval_days):
        teams = list(self.teams.all())
        num_teams = len(teams)

        if num_teams < 2:
            return f"Season {self} has insufficient teams."

        # Add a ghost team if the number of teams is odd (bye round)
        ghost_team = None
        if num_teams % 2 != 0:
            ghost_team = Team(name="BYE")
            teams.append(ghost_team)
            num_teams += 1

        # Fix the first team and rotate the remaining teams
        fixed_team = teams[0]
        rotating_teams = teams[1:]

        round_number = 1
        match_day_date = start_date

        # First round-robin: alternate home/away for each round
        for round_idx in range(num_teams - 1):  # We need n-1 rounds
            match_pairs = []

            # Pair fixed team with the first team in rotating list
            if round_idx % 2 == 0:
                match_pairs.append((fixed_team, rotating_teams[0]))
            else:
                match_pairs.append((rotating_teams[0], fixed_team))

            # Pair remaining teams
            for i in range(1, len(rotating_teams) // 2 + 1):
                home_team = rotating_teams[i]
                away_team = rotating_teams[-i]

                if round_idx % 2 == 0:
                    match_pairs.append((home_team, away_team))
                else:
                    match_pairs.append((away_team, home_team))

            # Create the match day and matches for this round
            self._create_match_day_and_matches(
                match_pairs, match_day_date, round_number
            )

            # Rotate the teams for the next round (excluding the fixed team)
            rotating_teams = [rotating_teams[-1]] + rotating_teams[:-1]

            round_number += 1
            match_day_date += timedelta(days=interval_days)

        # Second round-robin: swap home/away roles
        match_day_date += timedelta(days=interval_days)
        for round_idx in range(num_teams - 1):
            match_pairs = []

            # Pair fixed team with the first team in rotating list
            if round_idx % 2 == 0:
                match_pairs.append((rotating_teams[0], fixed_team))
            else:
                match_pairs.append((fixed_team, rotating_teams[0]))

            # Pair remaining teams, with home/away swapped
            for i in range(1, len(rotating_teams) // 2 + 1):
                home_team = rotating_teams[-i]
                away_team = rotating_teams[i]

                if round_idx % 2 == 0:
                    match_pairs.append((home_team, away_team))
                else:
                    match_pairs.append((away_team, home_team))

            # Create matches for this round
            self._create_match_day_and_matches(
                match_pairs, match_day_date, round_number
            )

            # Rotate the teams for the next round (excluding the fixed team)
            rotating_teams = [rotating_teams[-1]] + rotating_teams[:-1]

            round_number += 1
            match_day_date += timedelta(days=interval_days)

        return f"Matches generated for {self}."

    def _create_match_day_and_matches(self, match_pairs, match_day_date, round_number):
        match_day, _ = MatchDay.objects.get_or_create(
            season=self, round_number=round_number, date=match_day_date
        )
        for home_team, away_team in match_pairs:
            if home_team.name == "BYE" or away_team.name == "BYE":
                continue  # Skip "BYE" matches

            Match.objects.create(
                match_day=match_day,
                home_team=home_team,
                away_team=away_team,
                date=match_day_date,
            )

    class Meta:
        unique_together = ("year", "league")
        ordering = ["-year"]


class Team(models.Model):
    name = models.CharField(max_length=100)
    manager = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="managed_teams",
        null=True,
        blank=True,
    )
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def get_schedule(self, season):
        return self.home_matches.filter(
            match_day__season=season
        ) | self.away_matches.filter(match_day__season=season)

    def get_absolute_url(self):
        return reverse("team_detail", args=[str(self.pk)])

    def __str__(self):
        return self.name


class Player(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="player",
    )
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        return reverse("player_detail", args=[str(self.pk)])

    def get_current_team(self, season: Season):
        """
        Returns the team the player is currently part of for a given season.
        """
        try:
            season_team = self.teams.get(season=season)
            return season_team.team
        except SeasonTeam.DoesNotExist:
            return None


class SeasonTeam(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    players = models.ManyToManyField(Player, related_name="teams", blank=True)

    def __str__(self):
        return f"{self.team.name} in {self.season}"


class MatchDay(models.Model):
    season = models.ForeignKey(
        Season, on_delete=models.CASCADE, related_name="match_days"
    )
    round_number = models.IntegerField()
    date = models.DateField(db_index=True)

    def __str__(self):
        return f"Round {self.round_number} ({self.season})"

    class Meta:
        unique_together = ("season", "round_number")
        ordering = ["season", "round_number"]


class Match(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "Not Started"
        IN_PROGRESS = "In Progress"
        FINISHED = "Finished"

    match_day = models.ForeignKey(
        MatchDay, on_delete=models.CASCADE, related_name="matches"
    )
    home_team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="home_matches"
    )
    away_team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="away_matches"
    )
    date = models.DateField()
    status = models.CharField(max_length=20, choices=Status, default=Status.NOT_STARTED)

    class Meta:
        unique_together = ("match_day", "home_team", "away_team")
        ordering = ["match_day"]
        verbose_name_plural = "Matches"

    @property
    def home_score(self):
        if self.status == Match.Status.NOT_STARTED:
            return None
        segments = self.segments.all()
        if len(segments) == 0:
            return 0
        return sum(segment.home_score for segment in segments)

    @property
    def away_score(self):
        if self.status == Match.Status.NOT_STARTED:
            return None
        segments = self.segments.all()
        if len(segments) == 0:
            return 0
        return sum(segment.away_score for segment in segments)

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} on {self.date}"

    def clean(self):
        super().clean()
        if self.status != self.Status.NOT_STARTED and (
            self.home_score > 49 or self.away_score > 49
        ):
            raise ValidationError("The total score for a team cannot exceed 49 points.")


class SegmentScore(models.Model):
    class SegmentType(models.TextChoices):
        D1 = "D1", "Doubles 1"
        D2 = "D2", "Doubles 2"
        S1 = "S1", "Singles 1"
        D3 = "D3", "Doubles 3"
        S2 = "S2", "Singles 2"
        D4 = "D4", "Doubles 4"
        D5 = "D5", "Doubles 5"

    SEGMENT_GROUPS = {
        "group1": ["D1", "D2"],  # A player can only play once in D1 + D2
        "group2": ["S1", "D3", "S2"],  # A player can only play once in S1 + D3 + S2
        "group3": ["D4", "D5"],  # A player can only play once in D4 + D5
    }
    MAX_SCORE = 7

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="segments")
    segment_number = models.IntegerField()  # From 1 to 7
    home_score = models.IntegerField(null=True, blank=True)
    away_score = models.IntegerField(null=True, blank=True)
    segment_type = models.CharField(max_length=2, choices=SegmentType.choices)

    # Many-to-many relationship for players in each segment
    home_players = models.ManyToManyField(
        "Player", related_name="home_segments", blank=True
    )
    away_players = models.ManyToManyField(
        "Player", related_name="away_segments", blank=True
    )

    class Meta:
        unique_together = ("match", "segment_number")

    def __str__(self):
        return f"{self.match} - Segment {self.segment_type}"

    def clean(self):
        super().clean()

        # Validate correct number of players based on segment type
        self.validate_player_count(self.segment_type, self.home_players, "home")
        self.validate_player_count(self.segment_type, self.away_players, "away")

        # Validate player participation restrictions
        self.validate_player_participation(self.home_players, self.match, "home")
        self.validate_player_participation(self.away_players, self.match, "away")

    def validate_player_count(self, segment_type, players, team):
        """
        Validates that singles segments have exactly 1 player and doubles segments have exactly 2 players.
        """
        if segment_type.startswith("S") and players.count() > 1:
            raise ValidationError(
                f"{team.capitalize()} team must have exactly 1 player for singles segment {segment_type}."
            )
        elif segment_type.startswith("D") and players.count() not in [0, 2]:
            raise ValidationError(
                f"{team.capitalize()} team must have exactly 2 players for doubles segment {segment_type}."
            )

    def validate_player_participation(self, players, match, team_type):
        """
        Validates that players are not playing more than allowed in restricted segments.
        """
        for player in players.all():
            conflicting_segments = SegmentScore.objects.filter(
                match=match, **{f"{team_type}_players": player}
            ).exclude(pk=self.pk)  # Exclude the current segment

            # Keep track of player participation in restricted groups
            participation_tracker = {
                "group1": set(),
                "group2": set(),
                "group3": set(),
            }

            for segment in conflicting_segments:
                if segment.segment_type in self.SEGMENT_GROUPS["group1"]:
                    participation_tracker["group1"].add(segment.segment_type)
                elif segment.segment_type in self.SEGMENT_GROUPS["group2"]:
                    participation_tracker["group2"].add(segment.segment_type)
                elif segment.segment_type in self.SEGMENT_GROUPS["group3"]:
                    participation_tracker["group3"].add(segment.segment_type)

            # Add current segment type to the tracker
            if self.segment_type in self.SEGMENT_GROUPS["group1"]:
                participation_tracker["group1"].add(self.segment_type)
            elif self.segment_type in self.SEGMENT_GROUPS["group2"]:
                participation_tracker["group2"].add(self.segment_type)
            elif self.segment_type in self.SEGMENT_GROUPS["group3"]:
                participation_tracker["group3"].add(self.segment_type)

            # Now check if any player plays more than once in a restricted group
            for _, participation in participation_tracker.items():
                if len(participation) > 1:
                    raise ValidationError(
                        f"Player {player} cannot participate in multiple segments of the same group ({', '.join(participation)})."
                    )


class LeagueTable(models.Model):
    season = models.ForeignKey(
        Season, on_delete=models.CASCADE, related_name="league_table"
    )
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    draws = models.IntegerField(default=0)
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.team} - {self.points} points in {self.season}"
