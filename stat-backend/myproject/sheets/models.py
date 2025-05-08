from django.db import models

# models.py
from django.db import models
from django.contrib.auth.models import User

class Team(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=50)

class Player(models.Model):
    name = models.CharField(max_length=100)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    position = models.CharField(max_length=20, choices=[
        ('wing', 'Wing'),
        ('backcourt', 'Backcourt'),
        ('pivot', 'Pivot'),
        ('goalkeeper', 'Goalkeeper'),
    ])

class Match(models.Model):
    home_team = models.ForeignKey(Team, related_name='home_matches', on_delete=models.CASCADE)
    away_team = models.ForeignKey(Team, related_name='away_matches', on_delete=models.CASCADE)
    date = models.DateTimeField()
    home_score = models.IntegerField()
    away_score = models.IntegerField()


class MatchEvent(models.Model):
    EVENT_TYPES = [
        ('goal', 'Goal'),
        ('assist_goal', 'Assist (Goal)'),
        ('assist_no_goal', 'Assist (No Goal)'),
        ('steal', 'Steal'),
        ('block', 'Block'),
        ('penalty_drawn', 'Penalty Drawn'),
        ('suspension_drawn', 'Suspension Drawn'),
        ('missed_shot_6m', 'Missed Shot (6m)'),
        ('missed_shot_9m', 'Missed Shot (9m)'),
        ('turnover', 'Turnover'),
        ('suspension_conceded', 'Suspension Conceded'),
        ('penalty_conceded', 'Penalty Conceded'),
    ]
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    timestamp = models.DateTimeField()  # Match time (e.g., "00:15:30")
    period = models.IntegerField()      # 1st/2nd half, overtime
    goal_difference = models.IntegerField()  # e.g., +2, -1, 0

class PlayerScore(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    total_score = models.FloatField()  # Sum of weighted actions

    def calculate_score(self):
        events = MatchEvent.objects.filter(player=self.player, match=self.match)
        total = 0
        for event in events:
            weight = self._get_event_weight(event.event_type)
            time_factor = self._get_time_factor(event.timestamp)
            score_factor = self._get_score_factor(event.goal_difference)
            total += weight * time_factor * score_factor
        self.total_score = total
        self.save()

    def _get_event_weight(self, event_type):
        weights = {
            'goal': 1.0,
            'assist_goal': 0.6,
            'assist_no_goal': 0.4,
            'steal': 0.8,
            'block': 0.25,
            'penalty_drawn': 0.75,
            'suspension_drawn': 0.8,
            'missed_shot_6m': -0.7,
            'missed_shot_9m': -0.45,
            'turnover': -0.6,
            'suspension_conceded': -0.8,
            'penalty_conceded': -0.75,
        }
        return weights.get(event_type, 0)

    def _get_time_factor(self, timestamp):
        """Linear increase from 0.5 (start) to 1.5 (end)"""
        match_duration = 60  # minutes
        event_minute = timestamp.minute + timestamp.second / 60
        return 0.5 + (event_minute / match_duration)

    def _get_score_factor(self, goal_diff):
        """Bell curve: max weight at close scores (±1)"""
        return 2.0 / (1 + abs(goal_diff))