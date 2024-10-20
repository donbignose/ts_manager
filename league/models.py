from django.db import models
from django.contrib.auth.models import User


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

    def __str__(self):
        return self.name


class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class SeasonTeam(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    players = models.ManyToManyField(Player, related_name="teams")

    def __str__(self):
        return f"{self.team.name} in {self.season}"


class MatchDay(models.Model):
    season = models.ForeignKey(
        Season, on_delete=models.CASCADE, related_name="match_days"
    )
    round_number = models.IntegerField()

    def __str__(self):
        return f"Round {self.round_number} ({self.season})"

    class Meta:
        unique_together = ("season", "round_number")
        ordering = ["season", "round_number"]


class Match(models.Model):
    match_day = models.ForeignKey(
        MatchDay, on_delete=models.CASCADE, related_name="matches"
    )
    home_team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="home_matches"
    )
    away_team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name="away_matches"
    )
    match_date = models.DateField()

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} on {self.match_date}"


class SegmentScore(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="segments")
    segment_number = models.IntegerField()
    home_score = models.IntegerField()
    away_score = models.IntegerField()

    class Meta:
        unique_together = ("match", "segment_number")


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
