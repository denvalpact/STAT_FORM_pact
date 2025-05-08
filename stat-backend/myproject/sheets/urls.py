# urls.py
from django.urls import path
from .views import PlayerScoreListView, PlayerScoreDetailView

urlpatterns = [
    path('api/playerscores/', PlayerScoreListView.as_view(), name='playerscore-list'),
    path('api/playerscores/<int:pk>/', PlayerScoreDetailView.as_view(), name='playerscore-detail'),
]