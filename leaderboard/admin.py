from django.contrib import admin

from .models import Leaderboard, LeaderboardEntry, LeaderboardAction

admin.site.register(Leaderboard)
admin.site.register(LeaderboardEntry)
admin.site.register(LeaderboardAction)