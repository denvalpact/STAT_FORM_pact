from django.test import TestCase

# Create your tests here.
# tests.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Team, Player, Match, MatchEvent, PlayerScore

class PlayerScoreTests(TestCase):
    def setUp(self):
        # Create test data
        self.team1 = Team.objects.create(name="Spain", country="ES")
        self.team2 = Team.objects.create(name="Brazil", country="BR")
        
        self.player1 = Player.objects.create(
            name="Player A", 
            team=self.team1, 
            position="backcourt"
        )
        self.player2 = Player.objects.create(
            name="Player B", 
            team=self.team2, 
            position="wing"
        )
        
        self.match = Match.objects.create(
            home_team=self.team1,
            away_team=self.team2,
            home_score=30,
            away_score=25,
        )
        
        # API client
        self.client = APIClient()

        def test_match_creation(self):
            self.assertEqual(self.match.home_team.name, "Spain")
            self.assertEqual(self.match.away_score, 25)

    def test_player_score_calculation(self):
        # Create events for Player 1
        MatchEvent.objects.create(
            match=self.match,
            player=self.player1,
            event_type="goal",
            goal_difference=1,
        )
        MatchEvent.objects.create(
            match=self.match,
            player=self.player1,
            event_type="steal",
            goal_difference=2,
        )
        
        # Calculate PlayerScore
        player_score = PlayerScore.objects.create(
            player=self.player1,
            match=self.match,
        )
        player_score.calculate_score()
        
        # Expected: (1.0 * time_factor * score_factor) + (0.8 * time_factor * score_factor)
        # Assuming time_factor=1.0 and score_factor=2.0 for simplicity in tests
        expected_score = (1.0 * 1.0 * 2.0) + (0.8 * 1.0 * 2.0)
        self.assertAlmostEqual(player_score.total_score, expected_score, places=2)

        def test_player_score_api(self):
            # Create a PlayerScore entry
            PlayerScore.objects.create(
                player=self.player1,
                match=self.match,
                total_score=5.5,
            )
            
            # Fetch via API
            url = reverse('playerscore-list')
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]['total_score'], 5.5)

        def test_invalid_event_type(self):
            with self.assertRaises(ValueError):
                MatchEvent.objects.create(
                    match=self.match,
                    player=self.player1,
                    event_type="invalid_event",  # Should raise error
                    goal_difference=0,
                )

    def test_empty_player_score(self):
        player_score = PlayerScore.objects.create(
            player=self.player2,
            match=self.match,
        )
        player_score.calculate_score()
        self.assertEqual(player_score.total_score, 0.0)  # No events = 0 score

        def test_time_factor_calculation(self):
            player_score = PlayerScore.objects.create(
                player=self.player1,
                match=self.match,
            )
            # Test start of match (minute 0)
            self.assertAlmostEqual(
                player_score._get_time_factor("00:00:00"), 
                0.5, 
                places=2
            )
            # Test end of match (minute 60)
            self.assertAlmostEqual(
                player_score._get_time_factor("01:00:00"), 
                1.5, 
                places=2
            )

    def test_score_factor_calculation(self):
        player_score = PlayerScore.objects.create(
            player=self.player1,
            match=self.match,
        )
        # Close game (±1 goal)
        self.assertEqual(player_score._get_score_factor(1), 1.0)
        # Blowout (±5 goals)
        self.assertAlmostEqual(
            player_score._get_score_factor(5), 
            0.33, 
            places=2
        )



# Run tests using Django's test runner or pytest
# python manage.py test
# pytest