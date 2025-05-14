from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Team URLs
    path('teams/', views.team_list, name='team_list'),
    path('teams/create/', views.team_create, name='team_create'),
    path('teams/<int:pk>/', views.team_detail, name='team_detail'),
    
    # Match URLs
    path('matches/', views.match_list, name='match_list'),
    path('matches/create/', views.match_create, name='match_create'),
    path('matches/<int:pk>/', views.match_detail, name='match_detail'),
    path('matches/<int:pk>/manage/', views.match_manage, name='match_manage'),
    path('matches/<int:pk>/start/', views.match_start, name='match_start'),
    path('matches/<int:pk>/update-time/', views.match_update_time, name='match_update_time'),
    
    # Match Event URLs
    path('matches/<int:match_pk>/events/', views.match_event_create, name='match_event_create'),
    path('events/<int:event_pk>/delete/', views.match_event_delete, name='match_event_delete'),
    
    # Player URLs
    path('players/<int:pk>/', views.player_detail, name='player_detail'),
    
    # Statistics URLs
    path('players/<int:player_pk>/stats/', views.player_stats, name='player_stats'),
    path('teams/<int:team_pk>/stats/', views.team_stats, name='team_stats'),
    
    # API URLs
    path('api/matches/<int:pk>/events/', views.api_match_events, name='api_match_events'),
]

# Add this if you're using Django's admin interface
from django.contrib import admin
urlpatterns += [
    path('admin/', admin.site.urls),
]