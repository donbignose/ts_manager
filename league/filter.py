from league.models import Player
import django_filters as df


class PlayerFilter(df.FilterSet):
    first_name = df.CharFilter(lookup_expr="icontains", label="First Name")
    last_name = df.CharFilter(lookup_expr="icontains", label="Last Name")

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
        fields = ["first_name", "last_name"]
