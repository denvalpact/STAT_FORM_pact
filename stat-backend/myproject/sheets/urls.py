from django.urls import path
from . import views

urlpatterns = [
    path('matches/<int:match_id>/', views.match_dashboard, name='match-dashboard'),
    path('matches/<int:match_id>/stats/', views.player_stats, name='player-stats'),
    path('api/events/', views.record_event, name='record-event'),
    path('api/matches/<int:match_id>/', views.get_match_state, name='match-state'),
    path('api/players/', views.team_players, name='team-players'),
    path('api/stream/<int:match_id>/', views.live_event_stream, name='event-stream'),
]