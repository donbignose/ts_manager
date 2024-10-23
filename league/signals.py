from django.db.models.signals import post_save
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
