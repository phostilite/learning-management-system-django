# Generated by Django 5.1.1 on 2024-09-19 05:57

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Leaderboard',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='leaderboards', to='courses.course')),
                ('course_delivery', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='leaderboards', to='courses.delivery')),
            ],
        ),
        migrations.CreateModel(
            name='LeaderboardAction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('action_type', models.CharField(choices=[('QUIZ_COMPLETION', 'Quiz Completion'), ('COURSE_PROGRESS', 'Course Progress'), ('ASSIGNMENT_SUBMISSION', 'Assignment Submission'), ('DISCUSSION_PARTICIPATION', 'Discussion Participation'), ('CUSTOM', 'Custom Action')], max_length=30)),
                ('points', models.PositiveIntegerField()),
                ('description', models.CharField(max_length=255)),
                ('leaderboard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='leaderboard.leaderboard')),
            ],
        ),
        migrations.CreateModel(
            name='LeaderboardEntry',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('score', models.PositiveIntegerField(default=0)),
                ('rank', models.PositiveIntegerField(blank=True, null=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('leaderboard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entries', to='leaderboard.leaderboard')),
            ],
            options={
                'ordering': ['-score', 'last_updated'],
            },
        ),
    ]
