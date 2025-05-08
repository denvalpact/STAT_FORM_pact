from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Team, Player, Match, MatchEvent, PlayerScore

admin.site.register(Team)
admin.site.register(Player)
admin.site.register(Match)
admin.site.register(MatchEvent)
admin.site.register(PlayerScore)