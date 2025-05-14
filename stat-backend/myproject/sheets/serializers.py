from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Team, Player, Match, MatchEvent, 
    PlayerStat, Referee
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role']
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'required': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data['role']
        )
        return user

class TeamSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'short_code', 'coach', 'logo', 'logo_url', 'founded_year']
        extra_kwargs = {
            'logo': {'write_only': True}
        }
    
    def get_logo_url(self, obj):
        if obj.logo:
            return obj.logo.url
        return None

class PlayerSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    team = TeamSerializer(read_only=True)
    team_id = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(),
        source='team',
        write_only=True
    )
    position_display = serializers.CharField(
        source='get_position_display',
        read_only=True
    )
    
    class Meta:
        model = Player
        fields = [
            'id', 'user', 'team', 'team_id', 'number', 
            'position', 'position_display', 'is_captain'
        ]
        extra_kwargs = {
            'number': {'min_value': 1, 'max_value': 99}
        }
    
    def validate_number(self, value):
        team = self.initial_data.get('team_id')
        if team and Player.objects.filter(team=team, number=value).exists():
            raise serializers.ValidationError("This number is already taken for this team.")
        return value

class RefereeSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    
    class Meta:
        model = Referee
        fields = ['id', 'user', 'license_number']
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = UserSerializer.create(UserSerializer(), validated_data=user_data)
        referee = Referee.objects.create(user=user, **validated_data)
        return referee

class MatchSerializer(serializers.ModelSerializer):
    home_team = TeamSerializer(read_only=True)
    away_team = TeamSerializer(read_only=True)
    home_team_id = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(),
        source='home_team',
        write_only=True
    )
    away_team_id = serializers.PrimaryKeyRelatedField(
        queryset=Team.objects.all(),
        source='away_team',
        write_only=True
    )
    referees = RefereeSerializer(many=True, read_only=True)
    referee_ids = serializers.PrimaryKeyRelatedField(
        queryset=Referee.objects.all(),
        source='referees',
        many=True,
        write_only=True,
        required=False
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    formatted_time = serializers.CharField(
        source='get_formatted_time',
        read_only=True
    )
    score = serializers.CharField(
        source='get_score',
        read_only=True
    )
    
    class Meta:
        model = Match
        fields = [
            'id', 'home_team', 'away_team', 'home_team_id', 'away_team_id',
            'date', 'venue', 'status', 'status_display', 'current_time',
            'formatted_time', 'home_score', 'away_score', 'score', 'duration',
            'is_live', 'referees', 'referee_ids'
        ]
    
    def validate(self, data):
        if data['home_team'] == data['away_team']:
            raise serializers.ValidationError(
                {"away_team": "Home and away teams cannot be the same."}
            )
        return data

class MatchEventSerializer(serializers.ModelSerializer):
    match = serializers.PrimaryKeyRelatedField(queryset=Match.objects.all())
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    player = serializers.PrimaryKeyRelatedField(
        queryset=Player.objects.all(),
        allow_null=True
    )
    related_player = serializers.PrimaryKeyRelatedField(
        queryset=Player.objects.all(),
        allow_null=True
    )
    event_type_display = serializers.CharField(
        source='get_event_type_display',
        read_only=True
    )
    
    class Meta:
        model = MatchEvent
        fields = [
            'id', 'match', 'event_type', 'event_type_display', 'team',
            'player', 'related_player', 'period', 'time_seconds',
            'notes', 'timestamp'
        ]
    
    def validate(self, data):
        match = data.get('match')
        team = data.get('team')
        
        # Check if team is participating in the match
        if team and match and team not in [match.home_team, match.away_team]:
            raise serializers.ValidationError(
                {"team": "This team is not participating in the match."}
            )
        
        # Check if player belongs to the team
        player = data.get('player')
        if player and player.team != team:
            raise serializers.ValidationError(
                {"player": "This player doesn't belong to the specified team."}
            )
        
        # Check if related player belongs to either team
        related_player = data.get('related_player')
        if related_player and related_player.team not in [match.home_team, match.away_team]:
            raise serializers.ValidationError(
                {"related_player": "This player is not participating in the match."}
            )
        
        # Check if match is live
        if match and not match.is_live:
            raise serializers.ValidationError(
                {"match": "Cannot add events to a match that's not live."}
            )
        
        return data

class PlayerStatSerializer(serializers.ModelSerializer):
    player = PlayerSerializer(read_only=True)
    player_id = serializers.PrimaryKeyRelatedField(
        queryset=Player.objects.all(),
        source='player',
        write_only=True
    )
    match = MatchSerializer(read_only=True)
    match_id = serializers.PrimaryKeyRelatedField(
        queryset=Match.objects.all(),
        source='match',
        write_only=True
    )
    
    class Meta:
        model = PlayerStat
        fields = [
            'id', 'player', 'player_id', 'match', 'match_id',
            'goals', 'seven_m_goals', 'assists', 'steals', 'blocks',
            'turnovers', 'shots_taken', 'playing_time',
            'two_min_suspensions', 'yellow_cards', 'red_cards',
            'saves', 'conceded_goals', 'total_points', 'efficiency'
        ]
        read_only_fields = ['total_points', 'efficiency']

class MatchDetailSerializer(MatchSerializer):
    events = MatchEventSerializer(many=True, read_only=True)
    home_team_stats = serializers.SerializerMethodField()
    away_team_stats = serializers.SerializerMethodField()
    
    class Meta(MatchSerializer.Meta):
        fields = MatchSerializer.Meta.fields + ['events', 'home_team_stats', 'away_team_stats']
    
    def get_home_team_stats(self, obj):
        stats = PlayerStat.objects.filter(
            match=obj,
            player__team=obj.home_team
        )
        return PlayerStatSerializer(stats, many=True).data
    
    def get_away_team_stats(self, obj):
        stats = PlayerStat.objects.filter(
            match=obj,
            player__team=obj.away_team
        )
        return PlayerStatSerializer(stats, many=True).data

class PlayerDetailSerializer(PlayerSerializer):
    stats = serializers.SerializerMethodField()
    current_team = serializers.SerializerMethodField()
    
    class Meta(PlayerSerializer.Meta):
        fields = PlayerSerializer.Meta.fields + ['stats', 'current_team']
    
    def get_stats(self, obj):
        stats = PlayerStat.objects.filter(player=obj).order_by('-match__date')[:10]
        return PlayerStatSerializer(stats, many=True).data
    
    def get_current_team(self, obj):
        return TeamSerializer(obj.team).data

class TeamDetailSerializer(TeamSerializer):
    players = serializers.SerializerMethodField()
    upcoming_matches = serializers.SerializerMethodField()
    past_matches = serializers.SerializerMethodField()
    
    class Meta(TeamSerializer.Meta):
        fields = TeamSerializer.Meta.fields + ['players', 'upcoming_matches', 'past_matches']
    
    def get_players(self, obj):
        players = obj.players.all().order_by('number')
        return PlayerSerializer(players, many=True).data
    
    def get_upcoming_matches(self, obj):
        from django.utils import timezone
        matches = Match.objects.filter(
            models.Q(home_team=obj) | models.Q(away_team=obj),
            date__gte=timezone.now()
        ).order_by('date')[:5]
        return MatchSerializer(matches, many=True).data
    
    def get_past_matches(self, obj):
        from django.utils import timezone
        matches = Match.objects.filter(
            models.Q(home_team=obj) | models.Q(away_team=obj),
            date__lt=timezone.now()
        ).order_by('-date')[:5]
        return MatchSerializer(matches, many=True).data