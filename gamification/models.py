# gamification/models.py

from django.db import models
from django.conf import settings
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator

class UserGamificationProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gamification_profile')
    xp = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    streak_days = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Gamification Profile for {self.user.username}"

class Badge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='badges/')
    xp_value = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class UserBadge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'badge']

    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"

class Achievement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    xp_reward = models.PositiveIntegerField(default=0)
    badge = models.ForeignKey(Badge, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class UserAchievement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'achievement']

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"

class GamificationAction(models.Model):
    ACTION_TYPES = (
        ('COURSE_COMPLETION', 'Course Completion'),
        ('RESOURCE_COMPLETION', 'Resource Completion'),
        ('QUIZ_COMPLETION', 'Quiz Completion'),
        ('DAILY_LOGIN', 'Daily Login'),
        ('FORUM_POST', 'Forum Post'),
        ('HELP_OTHERS', 'Helping Others'),
        ('FEEDBACK_GIVEN', 'Feedback Given'),
        ('CUSTOM', 'Custom Action'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    xp_reward = models.PositiveIntegerField(default=0)
    cooldown_minutes = models.PositiveIntegerField(default=0, help_text="Minimum minutes between actions (0 for no cooldown)")
    daily_limit = models.PositiveIntegerField(default=0, help_text="Maximum times this action can be performed per day (0 for no limit)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_action_type_display()})"

class UserAction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gamification_actions')
    action = models.ForeignKey(GamificationAction, on_delete=models.CASCADE)
    performed_at = models.DateTimeField(auto_now_add=True)
    xp_earned = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.user.username} - {self.action.name} at {self.performed_at}"

class Level(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=100)
    xp_threshold = models.PositiveIntegerField()
    badge = models.ForeignKey(Badge, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['number']

    def __str__(self):
        return f"Level {self.number}: {self.name}"

class Quest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    xp_reward = models.PositiveIntegerField(default=0)
    badge_reward = models.ForeignKey(Badge, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class QuestTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='tasks')
    action = models.ForeignKey(GamificationAction, on_delete=models.CASCADE)
    required_count = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.quest.name} - {self.action.name} (x{self.required_count})"

class UserQuest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quests')
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE)
    progress = models.JSONField(default=dict)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'quest']

    def __str__(self):
        return f"{self.user.username} - {self.quest.name}"

class Reward(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    xp_cost = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class UserReward(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rewards')
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE)
    redeemed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.reward.name}"