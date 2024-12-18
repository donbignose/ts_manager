# Generated by Django 5.1.2 on 2024-10-28 11:34

import django.db.models.deletion
import django.db.models.expressions
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0012_delete_leaguetable'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeagueTable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('played', models.IntegerField(default=0)),
                ('wins', models.IntegerField(default=0)),
                ('draws', models.IntegerField(default=0)),
                ('losses', models.IntegerField(default=0)),
                ('points', models.GeneratedField(db_persist=True, expression=django.db.models.expressions.CombinedExpression(django.db.models.expressions.CombinedExpression(models.F('wins'), '*', models.Value(3)), '+', models.F('draws')), output_field=models.IntegerField())),
                ('goals_for', models.IntegerField(default=0)),
                ('goals_against', models.IntegerField(default=0)),
                ('goal_difference', models.GeneratedField(db_persist=True, expression=django.db.models.expressions.CombinedExpression(models.F('goals_for'), '-', models.F('goals_against')), output_field=models.IntegerField())),
                ('position', models.IntegerField(blank=True, null=True)),
                ('match_day', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='team_standings', to='league.matchday')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='standings', to='league.team')),
            ],
            options={
                'ordering': ['-points', '-goal_difference', '-goals_for'],
                'unique_together': {('team', 'match_day')},
            },
        ),
    ]
