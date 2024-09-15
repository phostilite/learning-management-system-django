# gamification/admin.py

from django.contrib import admin
from .models import (
    UserGamificationProfile,
    Badge,
    UserBadge,
    Achievement,
    UserAchievement,
    GamificationAction,
    UserAction,
    Level,
    Quest,
    QuestTask,
    UserQuest,
    Reward,
    UserReward
)

@admin.register(UserGamificationProfile)
class UserGamificationProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'xp', 'level', 'streak_days', 'last_activity_date')
    search_fields = ('user__username', 'user__email')
    list_filter = ('level', 'last_activity_date')

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'xp_value', 'is_active')
    search_fields = ('name', 'description')
    list_filter = ('is_active',)

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'earned_at')
    search_fields = ('user__username', 'badge__name')
    list_filter = ('earned_at', 'badge')

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'xp_reward', 'badge', 'is_active')
    search_fields = ('name', 'description')
    list_filter = ('is_active', 'badge')

@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'earned_at')
    search_fields = ('user__username', 'achievement__name')
    list_filter = ('earned_at', 'achievement')

@admin.register(GamificationAction)
class GamificationActionAdmin(admin.ModelAdmin):
    list_display = ('name', 'action_type', 'xp_reward', 'cooldown_minutes', 'daily_limit', 'is_active')
    search_fields = ('name',)
    list_filter = ('action_type', 'is_active')

@admin.register(UserAction)
class UserActionAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'performed_at', 'xp_earned')
    search_fields = ('user__username', 'action__name')
    list_filter = ('action', 'performed_at')

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('number', 'name', 'xp_threshold', 'badge')
    search_fields = ('name',)
    ordering = ('number',)

class QuestTaskInline(admin.TabularInline):
    model = QuestTask
    extra = 1

@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ('name', 'xp_reward', 'badge_reward', 'start_date', 'end_date', 'is_active')
    search_fields = ('name', 'description')
    list_filter = ('is_active', 'start_date', 'end_date')
    inlines = [QuestTaskInline]

@admin.register(UserQuest)
class UserQuestAdmin(admin.ModelAdmin):
    list_display = ('user', 'quest', 'started_at', 'completed_at')
    search_fields = ('user__username', 'quest__name')
    list_filter = ('started_at', 'completed_at')

@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    list_display = ('name', 'xp_cost', 'is_active')
    search_fields = ('name', 'description')
    list_filter = ('is_active',)

@admin.register(UserReward)
class UserRewardAdmin(admin.ModelAdmin):
    list_display = ('user', 'reward', 'redeemed_at')
    search_fields = ('user__username', 'reward__name')
    list_filter = ('redeemed_at',)