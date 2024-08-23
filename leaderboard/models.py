from django.db import models
from django.contrib.auth import get_user_model
from courses.models import Course, CourseDelivery
import uuid

User = get_user_model()

class Leaderboard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='leaderboards')
    course_delivery = models.ForeignKey(CourseDelivery, on_delete=models.CASCADE, related_name='leaderboards', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.course.title}"

class LeaderboardEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    leaderboard = models.ForeignKey(Leaderboard, on_delete=models.CASCADE, related_name='entries')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaderboard_entries')
    score = models.PositiveIntegerField(default=0)
    rank = models.PositiveIntegerField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('leaderboard', 'user')
        ordering = ['-score', 'last_updated']

    def __str__(self):
        return f"{self.user.username} - {self.leaderboard.title}"

class LeaderboardAction(models.Model):
    ACTION_TYPES = (
        ('QUIZ_COMPLETION', 'Quiz Completion'),
        ('COURSE_PROGRESS', 'Course Progress'),
        ('ASSIGNMENT_SUBMISSION', 'Assignment Submission'),
        ('DISCUSSION_PARTICIPATION', 'Discussion Participation'),
        ('CUSTOM', 'Custom Action'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    leaderboard = models.ForeignKey(Leaderboard, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    points = models.PositiveIntegerField()
    description = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.leaderboard.title}"