from django.shortcuts import render
from rest_framework import generics
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Match, PlayerStat, Player, Team
from .serializers import PlayerScoreSerializer

class PlayerScoreListView(generics.ListAPIView):
    queryset = PlayerStat.objects.all()
    serializer_class = PlayerScoreSerializer

class PlayerScoreDetailView(generics.RetrieveAPIView):
    queryset = PlayerStat.objects.all()
    serializer_class = PlayerScoreSerializer

@receiver(post_save, sender=Match)
def create_player_stats(sender, instance, created, **kwargs):
    """
    Signal to create PlayerStat entries for all players in a match when the match is created.
    """
    if created:
        # Get all players from both teams
        home_players = Player.objects.filter(team=instance.home_team)
        away_players = Player.objects.filter(team=instance.away_team)
        players = list(home_players) + list(away_players)

        # Create PlayerStat entries for each player
        for player in players:
            PlayerStat.objects.create(
                player=player,
                match=instance,
                goals=0,
                seven_m_goals=0,
                assists=0,
                steals=0,
                blocks=0,
                turnovers=0,
                two_min_suspensions=0,
                yellow_cards=0,
                red_cards=0,
                saves=0,
                conceded_goals=0,
                total_points=0,
                efficiency=0.0
            )