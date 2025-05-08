from django.shortcuts import render
from rest_framework import generics
from .models import PlayerScore
from .serializers import PlayerScoreSerializer
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Match, PlayerStats

class PlayerScoreListView(generics.ListAPIView):
    queryset = PlayerScore.objects.all()
    serializer_class = PlayerScoreSerializer

class PlayerScoreDetailView(generics.RetrieveAPIView):
    queryset = PlayerScore.objects.all()
    serializer_class = PlayerScoreSerializer

    @receiver(post_save, sender=Match)
    def create_player_stats(sender, instance, created, **kwargs):
        if created:
            players = list(instance.home_team.player_set.all()) + \
                      list(instance.away_team.player_set.all())
            
            for player in players[:20]:  # Ensure max 20 players
                PlayerStats.objects.create(player=player, match=instance)

                # Update or initialize player stats for the match
                PlayerStats.objects.update_or_create(
                    player=player, 
                    match=instance,
                    defaults={
                        'goals': 0,
                        'assists': 0,
                        'yellow_cards': 0,
                        'red_cards': 0,
                        'minutes_played': 0
                    }
                )
                