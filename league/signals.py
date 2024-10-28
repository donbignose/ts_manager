from django.db.models.signals import post_save
from .helper import update_standings_for_new_match_day
from django.dispatch import receiver
from .models import Match, SegmentScore


@receiver(post_save, sender=Match)
def create_segments_for_match(sender, instance, created, **kwargs):
    """
    Automatically create 7 segments (5 doubles, 2 singles) when a match is created.
    """
    if created:
        # Define the 7 segments in order
        segment_types = [
            SegmentScore.SegmentType.D1,  # Doubles 1
            SegmentScore.SegmentType.D2,  # Doubles 2
            SegmentScore.SegmentType.S1,  # Singles 1
            SegmentScore.SegmentType.D3,  # Doubles 3
            SegmentScore.SegmentType.S2,  # Singles 2
            SegmentScore.SegmentType.D4,  # Doubles 4
            SegmentScore.SegmentType.D5,  # Doubles 5
        ]

        for index, segment_type in enumerate(segment_types, start=1):
            SegmentScore.objects.create(
                match=instance,
                segment_number=index,  # Segment number 1 through 7
                segment_type=segment_type,
            )


@receiver(post_save, sender=Match)
def update_standings_on_match_update(sender, instance, **kwargs):
    """
    Signal handler to update standings only when all matches for a match day are finished.
    """
    match_day = instance.match_day

    if match_day.completed:
        update_standings_for_new_match_day(match_day)


@receiver(post_save, sender=SegmentScore)
def finish_match_on_finished_score(sender, instance, **kwargs):
    """
    Signal handler to finish the match when all segments have been scored.
    """
    match = instance.match
    if match.status in (Match.Status.FINISHED, Match.Status.NOT_STARTED):
        return
    finished_match_score_condition = (
        match.home_score == 49
        or match.away_score == 49
        or (match.home_score == 48 and match.away_score == 48)
    )
    if match.segments.count() == 7 and finished_match_score_condition:
        match.status = Match.Status.FINISHED
        match.save()
