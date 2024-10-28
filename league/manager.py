from django.db import models

from league.models import MatchDay


class LeagueTableManager(models.Manager):
    def get_previous_standings(self, current_match_day):
        """
        Retrieve the standings from the previous match day for a given current match day.
        """
        previous_match_day = (
            MatchDay.objects.filter(
                season=current_match_day.season,
                round_number__lt=current_match_day.round_number,
            )
            .order_by("-round_number")
            .first()
        )
        if previous_match_day:
            return self.filter(match_day=previous_match_day)
        return self.none()
