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
        ('center', 'Center'),
    ])
    age = models.IntegerField(null=True, blank=True)
    height_cm = models.FloatField(null=True, blank=True)
    weight_kg = models.FloatField(null=True, blank=True)
class Match(models.Model):
    home_team = models.ForeignKey(Team, related_name='home_matches', on_delete=models.CASCADE)
    away_team = models.ForeignKey(Team, related_name='away_matches', on_delete=models.CASCADE)
    start_time = models.DateTimeField()  # Real-world start time
    duration_minutes = models.IntegerField(default=60)  # Handball matches are 60 mins
    home_score = models.IntegerField()
    away_score = models.IntegerField()

    def get_team_stats(self):
        """Returns stats for both teams in a structured format."""
        teams = {
            'home': {
                'name': self.home_team.name,
                'players': [],
                'total_score': 0.0,
            },
            'away': {
                'name': self.away_team.name,
                'players': [],
                'total_score': 0.0,
            }
        }

        # Fetch all player stats for this match
        stats = PlayerStats.objects.filter(match=self).select_related('player', 'player__team')

        for stat in stats:
            team_key = 'home' if stat.player.team == self.home_team else 'away'
            teams[team_key]['players'].append({
                'id': stat.player.id,
                'name': stat.player.name,
                'goals': stat.goals,
                'assists': stat.assists,
                'steals': stat.steals,
                'total_score': stat.total_score,
            })
            teams[team_key]['total_score'] += stat.total_score

        return teams

class PlayerStats(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    
    # Performance metrics (simplified for clarity)
    goals = models.IntegerField(default=0)
    assists = models.IntegerField(default=0)
    steals = models.IntegerField(default=0)
    blocks = models.IntegerField(default=0)
    turnovers = models.IntegerField(default=0)
    suspensions = models.IntegerField(default=0)
    
    # Calculated PlayerScore
    total_score = models.FloatField(default=0.0)

    def calculate_score(self):
        """Calculate PlayerScore based on weighted actions."""
        weights = {
            'goals': 1.0,
            'assists': 0.6,
            'steals': 0.8,
            'blocks': 0.25,
            'turnovers': -0.6,
            'suspensions': -0.8,
        }
        self.total_score = sum(
            getattr(self, stat) * weight 
            for stat, weight in weights.items()
        )
        self.save()


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
    match_time_seconds = models.IntegerField()  # Seconds into the match (0-3600 for 60 mins)
    period = models.IntegerField(choices=[(1, 'First Half'), (2, 'Second Half'), (3, 'Overtime')])
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

    def _get_time_factor(self, match_time_seconds):
        """Linear increase from 0.5 (start) to 1.5 (end) based on match progress."""
        match_duration_seconds = self.match.duration_minutes * 60
        progress = match_time_seconds / match_duration_seconds  # 0.0 to 1.0
        return 0.5 + progress  # 0.5 (start) to 1.5 (end)

    def _get_score_factor(self, goal_diff):
        """Bell curve: max weight at close scores (±1)"""
        return 2.0 / (1 + abs(goal_diff))