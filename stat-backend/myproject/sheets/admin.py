from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django import forms
from .models import Team, Player, Match, Referee, MatchEvent, PlayerStat

class PlayerAdminForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = '__all__'
        widgets = {
            'position': forms.Select(choices=Player.POSITION_CHOICES),
        }

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_code', 'player_count')
    search_fields = ('name', 'short_code')
    
    def player_count(self, obj):
        return obj.players.count()
    player_count.short_description = 'Players'

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    form = PlayerAdminForm
    list_display = ('number', 'name', 'team', 'position', 'is_captain')
    list_filter = ('team', 'position')
    search_fields = ('name', 'number')
    list_editable = ('is_captain',)
    ordering = ('team', 'number')

class MatchEventInline(admin.TabularInline):
    model = MatchEvent
    extra = 0
    fields = ('event_type', 'team', 'player', 'related_player', 'period', 'time_seconds', 'notes', 'timestamp')
    readonly_fields = ('timestamp',)
    autocomplete_fields = ('player', 'related_player')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ['player', 'related_player']:
            match_id = request.resolver_match.kwargs.get('object_id')
            if match_id:
                match = Match.objects.get(pk=match_id)
                kwargs['queryset'] = Player.objects.filter(
                    models.Q(team=match.home_team) | models.Q(team=match.away_team)
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class PlayerStatInline(admin.TabularInline):
    model = PlayerStat
    extra = 0
    fields = ('player', 'goals', 'seven_m_goals', 'assists', 'steals', 'blocks', 'turnovers')
    readonly_fields = ('player',)
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('match_display', 'date', 'status', 'score_display', 'time_display')
    list_filter = ('status', 'date')
    search_fields = ('home_team__name', 'away_team__name')
    inlines = [MatchEventInline, PlayerStatInline]
    autocomplete_fields = ('home_team', 'away_team', 'referees')
    actions = ['update_player_stats']
    fieldsets = (
        (None, {
            'fields': ('home_team', 'away_team', 'date', 'venue')
        }),
        ('Match Status', {
            'fields': ('status', 'current_time', 'home_score', 'away_score')
        }),
        ('Officials', {
            'fields': ('referees',),
            'classes': ('collapse',)
        }),
    )
    
    def match_display(self, obj):
        return f"{obj.home_team} vs {obj.away_team}"
    match_display.short_description = 'Match'
    
    def score_display(self, obj):
        return f"{obj.home_score} - {obj.away_score}"
    score_display.short_description = 'Score'
    
    def time_display(self, obj):
        return obj.get_formatted_time()
    time_display.short_description = 'Time'
    
    def update_player_stats(self, request, queryset):
        for match in queryset:
            for event in match.events.all():
                stat, created = PlayerStat.objects.get_or_create(
                    match=match,
                    player=event.player
                )
                if event.event_type == 'GOAL':
                    stat.goals += 1
                elif event.event_type == '7M_GOAL':
                    stat.seven_m_goals += 1
                elif event.event_type == 'ASSIST':
                    stat.assists += 1
                elif event.event_type == 'STEAL':
                    stat.steals += 1
                elif event.event_type == 'BLOCK':
                    stat.blocks += 1
                elif event.event_type == 'TURNOVER':
                    stat.turnovers += 1
                stat.save()
        self.message_user(request, f"Updated stats for {queryset.count()} matches")
    update_player_stats.short_description = "Update player stats from events"

@admin.register(Referee)
class RefereeAdmin(admin.ModelAdmin):
    list_display = ('name', 'license_number')
    search_fields = ('name', 'license_number')

@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'team', 'player', 'match_link', 'period', 'time_display')
    list_filter = ('event_type', 'team', 'period')
    search_fields = ('player__name', 'team__name')
    autocomplete_fields = ('match', 'team', 'player', 'related_player')
    readonly_fields = ('timestamp',)
    
    def match_link(self, obj):
        url = reverse('admin:stats_match_change', args=[obj.match.id])
        return format_html('<a href="{}">{}</a>', url, obj.match)
    match_link.short_description = 'Match'
    
    def time_display(self, obj):
        minutes = obj.time_seconds // 60
        seconds = obj.time_seconds % 60
        return f"{minutes}:{seconds:02d}"
    time_display.short_description = 'Time'

@admin.register(PlayerStat)
class PlayerStatAdmin(admin.ModelAdmin):
    list_display = ('player', 'team', 'match', 'goals', 'assists', 'total_points')
    list_filter = ('match', 'player__team')
    search_fields = ('player__name',)
    readonly_fields = ('efficiency',)
    
    def team(self, obj):
        return obj.player.team
    team.short_description = 'Team'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('player', 'player__team', 'match')