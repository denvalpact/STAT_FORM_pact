from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Team(models.Model):
    name = models.CharField(max_length=100)
    short_code = models.CharField(max_length=3, default='T')  # e.g., 'A', 'B'
    coach = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return self.name

class Player(models.Model):
    POSITION_CHOICES = [
        ('GK', 'Goalkeeper'),
        ('LW', 'Left Wing'),
        ('RW', 'Right Wing'),
        ('LB', 'Left Back'),
        ('RB', 'Right Back'),
        ('PV', 'Pivot'),
        ('CB', 'Center Back'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    number = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(99)]
    )
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=2, choices=POSITION_CHOICES)
    is_captain = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('team', 'number')
        ordering = ['number']
    
    def __str__(self):
        return f"{self.number} - {self.name} ({self.get_position_display()})"

class Match(models.Model):
    STATUS_CHOICES = [
        ('NS', 'Not Started'),
        ('1H', 'First Half'),
        ('HT', 'Half Time'),
        ('2H', 'Second Half'),
        ('OT', 'Overtime'),
        ('FT', 'Full Time'),
    ]
    
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    date = models.DateTimeField()
    venue = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='NS')
    current_time = models.PositiveIntegerField(default=0)  # in seconds
    home_score = models.PositiveIntegerField(default=0)
    away_score = models.PositiveIntegerField(default=0)
    
    referees = models.ManyToManyField('Referee', blank=True)
    
    def __str__(self):
        return f"{self.home_team} vs {self.away_team} - {self.date.date()}"
    
    def get_score(self):
        return f"{self.home_score} - {self.away_score}"
    
    def get_formatted_time(self):
        minutes = self.current_time // 60
        seconds = self.current_time % 60
        return f"{minutes}:{seconds:02d}"

class Referee(models.Model):
    name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return self.name

class MatchEvent(models.Model):
    EVENT_TYPES = [
        ('GOAL', 'Goal'),
        ('7M_GOAL', '7m Goal'),
        ('ASSIST', 'Assist'),
        ('STEAL', 'Steal'),
        ('BLOCK', 'Block'),
        ('TURNOVER', 'Turnover'),
        ('2MIN', '2-minute Suspension'),
        ('RED', 'Red Card'),
        ('YELLOW', 'Yellow Card'),
        ('TIMEOUT', 'Timeout'),
        ('PENALTY', 'Penalty'),
    ]
    
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, blank=True)
    related_player = models.ForeignKey(
        Player, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='related_events'
    )
    period = models.PositiveIntegerField(default=1)  # 1=1st half, 2=2nd half, 3=OT
    time_seconds = models.PositiveIntegerField()  # seconds into the period
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['period', 'time_seconds']
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.player} at {self.time_seconds}s"
    
    def save(self, *args, **kwargs):
        # Update match score if this is a goal event
        if self.event_type in ['GOAL', '7M_GOAL']:
            if self.team == self.match.home_team:
                self.match.home_score += 1
            else:
                self.match.away_score += 1
            self.match.save()
        super().save(*args, **kwargs)

class PlayerStat(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    
    # Basic stats
    goals = models.PositiveIntegerField(default=0)
    seven_m_goals = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    steals = models.PositiveIntegerField(default=0)
    blocks = models.PositiveIntegerField(default=0)
    turnovers = models.PositiveIntegerField(default=0)
    
    # Suspensions
    two_min_suspensions = models.PositiveIntegerField(default=0)
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)
    
    # Goalkeeper specific
    saves = models.PositiveIntegerField(default=0)
    conceded_goals = models.PositiveIntegerField(default=0)
    
    # Calculated fields
    total_points = models.PositiveIntegerField(default=0)
    efficiency = models.FloatField(default=0)
    
    class Meta:
        unique_together = ('match', 'player')
    
    def __str__(self):
        return f"{self.player} - {self.match}"
    
    def calculate_stats(self):
        # Calculate total points (goals + assists)
        self.total_points = self.goals + self.seven_m_goals + self.assists
        
        # Simple efficiency calculation (can be customized)
        if self.player.position == 'GK':
            total_shots = self.saves + self.conceded_goals
            self.efficiency = (self.saves / total_shots * 100) if total_shots > 0 else 0
        else:
            positive_actions = self.goals + self.seven_m_goals + self.assists + self.steals + self.blocks
            negative_actions = self.turnovers + self.two_min_suspensions
            total_actions = positive_actions + negative_actions
            self.efficiency = (positive_actions / total_actions * 100) if total_actions > 0 else 0
        
        self.save()