from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Team, Player, Match, MatchEvent, Referee, PlayerStat
from django.core.files.uploadedfile import SimpleUploadedFile
import datetime

class ModelTests(TestCase):
    def setUp(self):
        # Create test data
        self.team1 = Team.objects.create(
            name="Team Alpha", 
            short_code="ALP",
            coach="John Doe"
        )
        self.team2 = Team.objects.create(
            name="Team Beta", 
            short_code="BET",
            coach="Jane Smith"
        )
        
        self.user1 = User.objects.create_user(
            username='referee1',
            password='testpass123',
            role='REFEREE'
        )
        self.user2 = User.objects.create_user(
            username='player1',
            password='testpass123',
            role='PLAYER'
        )
        
        self.referee = Referee.objects.create(
            user=self.user1,
            license_number="REF12345"
        )
        
        self.player = Player.objects.create(
            user=self.user2,
            team=self.team1,
            number=10,
            position='PV',
            is_captain=True
        )
        
        self.match = Match.objects.create(
            home_team=self.team1,
            away_team=self.team2,
            date=datetime.datetime.now() + datetime.timedelta(days=1),
            venue="Main Arena"
        )
        self.match.referees.add(self.referee)

    def test_team_creation(self):
        self.assertEqual(self.team1.name, "Team Alpha")
        self.assertEqual(self.team1.short_code, "ALP")
        self.assertEqual(str(self.team1), "Team Alpha")

    def test_player_creation(self):
        self.assertEqual(self.player.number, 10)
        self.assertEqual(self.player.get_position_display(), "Pivot")
        self.assertEqual(str(self.player), "10 - player1 (Pivot)")

    def test_match_creation(self):
        self.assertEqual(self.match.home_team, self.team1)
        self.assertEqual(self.match.away_team, self.team2)
        self.assertEqual(self.match.status, "NS")
        self.assertEqual(self.match.referees.count(), 1)

    def test_match_event_creation(self):
        event = MatchEvent.objects.create(
            match=self.match,
            event_type='GOAL',
            team=self.team1,
            player=self.player,
            period=1,
            time_seconds=120
        )
        self.assertEqual(event.match, self.match)
        self.assertEqual(event.event_type, "GOAL")
        self.assertEqual(event.team, self.team1)
        
        # Test score update
        self.assertEqual(self.match.home_score, 1)

    def test_player_stat_creation(self):
        stat = PlayerStat.objects.create(
            match=self.match,
            player=self.player,
            goals=2,
            assists=1,
            saves=0
        )
        stat.calculate_stats()
        self.assertEqual(stat.total_points, 3)
        self.assertGreater(stat.efficiency, 0)

    def test_invalid_player_number(self):
        with self.assertRaises(ValidationError):
            player = Player(
                user=self.user2,
                team=self.team1,
                number=100,  # Invalid number
                position='LW'
            )
            player.full_clean()

    def test_same_team_match(self):
        with self.assertRaises(ValidationError):
            match = Match(
                home_team=self.team1,
                away_team=self.team1,
                date=datetime.datetime.now()
            )
            match.full_clean()

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='adminpass',
            role='LEAGUE_OFFICIAL'
        )
        self.referee_user = User.objects.create_user(
            username='referee',
            password='testpass',
            role='REFEREE'
        )
        self.team = Team.objects.create(name="Test Team", short_code="TST")
        
        # Create referee profile
        Referee.objects.create(user=self.referee_user, license_number="TEST123")
        
        self.match = Match.objects.create(
            home_team=self.team,
            away_team=Team.objects.create(name="Opponent", short_code="OPP"),
            date=datetime.datetime.now()
        )

    def test_dashboard_access(self):
        # Test unauthenticated access
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test authenticated access
        self.client.login(username='referee', password='testpass')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_team_list_view(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(reverse('team_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Team")

    def test_match_creation_view(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('match_create'), {
            'home_team': self.team.id,
            'away_team': Team.objects.create(name="New Team", short_code="NEW").id,
            'date': (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M'),
            'venue': "Test Arena"
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(Match.objects.count(), 2)

    def test_match_management_auth(self):
        # Test referee access to their match
        self.match.referees.add(Referee.objects.get(user=self.referee_user))
        self.client.login(username='referee', password='testpass')
        response = self.client.get(reverse('match_manage', args=[self.match.id]))
        self.assertEqual(response.status_code, 200)
        
        # Test unauthorized access
        other_user = User.objects.create_user(username='other', password='testpass', role='PLAYER')
        self.client.login(username='other', password='testpass')
        response = self.client.get(reverse('match_manage', args=[self.match.id]))
        self.assertEqual(response.status_code, 403)

    def test_match_event_creation(self):
        player = Player.objects.create(
            user=User.objects.create_user(username='testplayer', password='testpass', role='PLAYER'),
            team=self.team,
            number=7,
            position='PV'
        )
        
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(reverse('match_event_create', args=[self.match.id]), {
            'event_type': 'GOAL',
            'team': self.team.id,
            'player': player.id,
            'period': 1,
            'time_seconds': 300
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.match.events.count(), 1)
        self.assertEqual(self.match.home_score, 1)

class APITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.team1 = Team.objects.create(name="API Team 1", short_code="AT1")
        self.team2 = Team.objects.create(name="API Team 2", short_code="AT2")
        self.match = Match.objects.create(
            home_team=self.team1,
            away_team=self.team2,
            date=datetime.datetime.now()
        )
        self.player = Player.objects.create(
            user=User.objects.create_user(username='apiuser', password='testpass', role='PLAYER'),
            team=self.team1,
            number=9,
            position='LW'
        )
        MatchEvent.objects.create(
            match=self.match,
            event_type='GOAL',
            team=self.team1,
            player=self.player,
            period=1,
            time_seconds=120
        )

    def test_match_events_api(self):
        response = self.client.get(reverse('api_match_events', args=[self.match.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['match']['home_team'], "API Team 1")
        self.assertEqual(data['match']['away_team'], "API Team 2")
        self.assertEqual(len(data['events']), 1)
        self.assertEqual(data['events'][0]['event_type'], "Goal")

class AuthenticationTests(TestCase):
    def test_user_roles(self):
        official = User.objects.create_user(username='official', role='LEAGUE_OFFICIAL')
        referee = User.objects.create_user(username='referee', role='REFEREE')
        manager = User.objects.create_user(username='manager', role='MANAGER')
        player = User.objects.create_user(username='player', role='PLAYER')
        
        self.assertEqual(official.role, 'LEAGUE_OFFICIAL')
        self.assertEqual(referee.role, 'REFEREE')
        self.assertEqual(manager.role, 'MANAGER')
        self.assertEqual(player.role, 'PLAYER')

    def test_referee_profile_creation(self):
        user = User.objects.create_user(username='newref', password='testpass', role='REFEREE')
        referee = Referee.objects.create(user=user, license_number="NEW123")
        self.assertEqual(referee.user.username, 'newref')
        self.assertEqual(referee.license_number, 'NEW123')