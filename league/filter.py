from django.db.models import Q
from django.forms import TextInput
from league.forms import PlayerFilterForm
from league.models import Player
import django_filters as df


class PlayerFilter(df.FilterSet):
    name = df.CharFilter(
        method="filter_by_name",
        label="",
        widget=TextInput(
            attrs={
                "placeholder": "Search players",
                "class": "dark:bg-gray-700 dark:text-white dark:border-black",
            }
        ),
    )

    o = df.OrderingFilter(
        fields=(
            ("first_name", "first_name"),
            ("last_name", "last_name"),
        ),
        field_labels={
            "first_name": "First Name",
            "last_name": "Last Name",
        },
        label="Order by",
    )

    class Meta:
        model = Player
        fields = ["name"]
        form = PlayerFilterForm

    def filter_by_name(self, queryset, name, value):
        """
        Custom method to filter by first name or last name.
        This allows searching for either first or last name in one field.
        """
        return queryset.filter(
            Q(first_name__icontains=value) | Q(last_name__icontains=value)
        )
