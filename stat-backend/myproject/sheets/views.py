from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from .models import *
from .forms import *

# Helper functions
def is_league_official(user):
    return user.role == 'LEAGUE_OFFICIAL'

def is_referee(user):
    return user.role == 'REFEREE'

def is_manager(user):
    return user.role == 'MANAGER'

def is_player(user):
    return user.role == 'PLAYER'

# Dashboard Views
@login_required
def dashboard(request):
    context = {}
    if request.user.role == 'LEAGUE_OFFICIAL':
        context['matches'] = Match.objects.all().order_by('-date')[:5]
        context['teams'] = Team.objects.all()
    elif request.user.role == 'REFEREE':
        context['matches'] = Match.objects.filter(
            referees__user=request.user
        ).order_by('-date')[:5]
    elif request.user.role == 'MANAGER':
        # Assuming manager is associated with a team via their user profile
        try:
            team = request.user.player_profile.team
            context['matches'] = Match.objects.filter(
                models.Q(home_team=team) | models.Q(away_team=team)
            ).order_by('-date')[:5]
            context['team'] = team
        except:
            pass
    elif request.user.role == 'PLAYER':
        try:
            player = request.user.player_profile
            context['matches'] = Match.objects.filter(
                models.Q(home_team=player.team) | models.Q(away_team=player.team)
            ).order_by('-date')[:5]
            context['player'] = player
        except:
            pass
    
    return render(request, 'dashboard.html', context)

# Team Views
@login_required
@user_passes_test(is_league_official)
def team_list(request):
    teams = Team.objects.all().order_by('name')
    return render(request, 'teams/list.html', {'teams': teams})

@login_required
@user_passes_test(is_league_official)
def team_detail(request, pk):
    team = get_object_or_404(Team, pk=pk)
    players = team.players.all().order_by('number')
    matches = Match.objects.filter(
        models.Q(home_team=team) | models.Q(away_team=team)
    ).order_by('-date')
    
    return render(request, 'teams/detail.html', {
        'team': team,
        'players': players,
        'matches': matches
    })

@login_required
@user_passes_test(is_league_official)
def team_create(request):
    if request.method == 'POST':
        form = TeamForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('team_list')
    else:
        form = TeamForm()
    return render(request, 'teams/form.html', {'form': form})

# Match Views
@login_required
def match_list(request):
    matches = Match.objects.all().order_by('-date')
    return render(request, 'matches/list.html', {'matches': matches})

@login_required
def match_detail(request, pk):
    match = get_object_or_404(Match, pk=pk)
    events = match.events.all().order_by('period', 'time_seconds')
    
    # Check if user is authorized to manage this match
    can_manage = False
    if request.user.role == 'LEAGUE_OFFICIAL':
        can_manage = True
    elif request.user.role == 'REFEREE' and match.referees.filter(user=request.user).exists():
        can_manage = True
    
    return render(request, 'matches/detail.html', {
        'match': match,
        'events': events,
        'can_manage': can_manage
    })

@login_required
@user_passes_test(is_league_official)
def match_create(request):
    if request.method == 'POST':
        form = MatchForm(request.POST)
        if form.is_valid():
            match = form.save()
            return redirect('match_detail', pk=match.pk)
    else:
        form = MatchForm()
    return render(request, 'matches/form.html', {'form': form})

@login_required
def match_manage(request, pk):
    match = get_object_or_404(Match, pk=pk)
    
    # Authorization check
    if not (request.user.role == 'LEAGUE_OFFICIAL' or 
            match.referees.filter(user=request.user).exists()):
        raise PermissionDenied
    
    if request.method == 'POST':
        form = MatchManagementForm(request.POST, instance=match)
        if form.is_valid():
            form.save()
            return redirect('match_detail', pk=match.pk)
    else:
        form = MatchManagementForm(instance=match)
    
    return render(request, 'matches/manage.html', {
        'match': match,
        'form': form
    })

# Match Event Views
@login_required
@require_http_methods(['POST'])
def match_event_create(request, match_pk):
    match = get_object_or_404(Match, pk=match_pk)
    
    # Authorization check
    if not (request.user.role == 'LEAGUE_OFFICIAL' or 
            match.referees.filter(user=request.user).exists()):
        return HttpResponseForbidden()
    
    form = MatchEventForm(request.POST)
    if form.is_valid():
        event = form.save(commit=False)
        event.match = match
        event.save()
        return JsonResponse({'success': True, 'event_id': event.id})
    
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@login_required
@require_http_methods(['DELETE'])
def match_event_delete(request, event_pk):
    event = get_object_or_404(MatchEvent, pk=event_pk)
    
    # Authorization check
    if not (request.user.role == 'LEAGUE_OFFICIAL' or 
            event.match.referees.filter(user=request.user).exists()):
        return HttpResponseForbidden()
    
    event.delete()
    return JsonResponse({'success': True})

# Live Match Views
@login_required
def match_start(request, pk):
    match = get_object_or_404(Match, pk=pk)
    
    # Authorization check
    if not (request.user.role == 'LEAGUE_OFFICIAL' or 
            match.referees.filter(user=request.user).exists()):
        raise PermissionDenied
    
    match.status = '1H'
    match.is_live = True
    match.save()
    return redirect('match_manage', pk=match.pk)

@login_required
def match_update_time(request, pk):
    match = get_object_or_404(Match, pk=pk)
    
    # Authorization check
    if not (request.user.role == 'LEAGUE_OFFICIAL' or 
            match.referees.filter(user=request.user).exists()):
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        current_time = int(request.POST.get('current_time', 0))
        match.current_time = current_time
        
        # Update match status based on time
        if match.status == '1H' and current_time >= match.duration // 2:
            match.status = 'HT'
        elif match.status == 'HT' and current_time < match.duration // 2:
            match.status = '2H'
        elif match.status == '2H' and current_time >= match.duration:
            match.status = 'FT'
            match.is_live = False
        
        match.save()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False}, status=400)

# Player Views
@login_required
def player_detail(request, pk):
    player = get_object_or_404(Player, pk=pk)
    stats = PlayerStat.objects.filter(player=player).order_by('-match__date')
    
    # Authorization check - only league officials or team members can view
    if not (request.user.role == 'LEAGUE_OFFICIAL' or 
            (hasattr(request.user, 'player_profile') and 
             request.user.player_profile.team == player.team)):
        raise PermissionDenied
    
    return render(request, 'players/detail.html', {
        'player': player,
        'stats': stats
    })

# API Views
@login_required
def api_match_events(request, pk):
    match = get_object_or_404(Match, pk=pk)
    events = match.events.all().order_by('period', 'time_seconds')
    
    data = {
        'match': {
            'home_team': match.home_team.name,
            'away_team': match.away_team.name,
            'home_score': match.home_score,
            'away_score': match.away_score,
            'status': match.get_status_display(),
            'current_time': match.get_formatted_time(),
        },
        'events': [{
            'id': e.id,
            'event_type': e.get_event_type_display(),
            'team': e.team.name,
            'player': e.player.user.get_full_name() if e.player else '',
            'period': e.period,
            'time': e.time_seconds,
            'notes': e.notes,
        } for e in events]
    }
    
    return JsonResponse(data)

# Statistics Views
@login_required
def player_stats(request, player_pk):
    player = get_object_or_404(Player, pk=player_pk)
    stats = PlayerStat.objects.filter(player=player).order_by('-match__date')
    
    # Authorization check
    if not (request.user.role == 'LEAGUE_OFFICIAL' or 
            (hasattr(request.user, 'player_profile') and 
             request.user.player_profile.team == player.team)):
        raise PermissionDenied
    
    return render(request, 'stats/player.html', {
        'player': player,
        'stats': stats
    })

@login_required
def team_stats(request, team_pk):
    team = get_object_or_404(Team, pk=team_pk)
    players = team.players.all()
    matches = Match.objects.filter(
        models.Q(home_team=team) | models.Q(away_team=team)
    ).order_by('-date')
    
    # Calculate aggregate stats
    stats = {
        'goals': sum(p.goals for p in PlayerStat.objects.filter(player__team=team)),
        'assists': sum(p.assists for p in PlayerStat.objects.filter(player__team=team)),
        'saves': sum(p.saves for p in PlayerStat.objects.filter(player__team=team, player__position='GK')),
    }
    
    return render(request, 'stats/team.html', {
        'team': team,
        'players': players,
        'matches': matches,
        'stats': stats
    })