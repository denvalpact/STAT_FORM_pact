# serializers.py
from rest_framework import serializers
from .models import Player, Match, PlayerScore

class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ['id', 'name', 'position', 'team']

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = ['id', 'home_team', 'away_team', 'date', 'home_score', 'away_score']

class PlayerScoreSerializer(serializers.ModelSerializer):
    player = PlayerSerializer()
    match = MatchSerializer()
    class Meta:
        model = PlayerScore
        fields = ['player', 'match', 'total_score']
        depth = 1