from django.shortcuts import render
from rest_framework import generics
from .models import PlayerScore
from .serializers import PlayerScoreSerializer

class PlayerScoreListView(generics.ListAPIView):
    queryset = PlayerScore.objects.all()
    serializer_class = PlayerScoreSerializer

class PlayerScoreDetailView(generics.RetrieveAPIView):
    queryset = PlayerScore.objects.all()
    serializer_class = PlayerScoreSerializer