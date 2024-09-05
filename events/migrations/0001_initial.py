# Generated by Django 5.0.6 on 2024-09-05 09:02

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('event_type', models.CharField(choices=[('LECTURE', 'Lecture'), ('WEBINAR', 'Webinar'), ('WORKSHOP', 'Workshop'), ('EXAM', 'Exam'), ('ASSIGNMENT_DUE', 'Assignment Due'), ('COURSE_START', 'Course Start'), ('COURSE_END', 'Course End'), ('OFFICE_HOURS', 'Office Hours'), ('GROUP_MEETING', 'Group Meeting'), ('GUEST_SPEAKER', 'Guest Speaker'), ('ORIENTATION', 'Orientation'), ('DEADLINE', 'Deadline'), ('OTHER', 'Other')], max_length=20)),
                ('start_datetime', models.DateTimeField()),
                ('end_datetime', models.DateTimeField()),
                ('is_all_day', models.BooleanField(default=False)),
                ('location', models.CharField(blank=True, max_length=255, null=True)),
                ('is_virtual', models.BooleanField(default=False)),
                ('virtual_meeting_link', models.URLField(blank=True, null=True)),
                ('max_participants', models.PositiveIntegerField(blank=True, null=True)),
                ('is_public', models.BooleanField(default=True)),
                ('is_mandatory', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('object_id', models.UUIDField(blank=True, null=True)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('organizer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='organized_events', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='EventGroup',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='groups', to='events.event')),
                ('members', models.ManyToManyField(related_name='event_groups', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='EventReminder',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('reminder_type', models.CharField(choices=[('EMAIL', 'Email'), ('SMS', 'SMS'), ('PUSH', 'Push Notification')], max_length=10)),
                ('remind_before', models.DurationField()),
                ('is_sent', models.BooleanField(default=False)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reminders', to='events.event')),
            ],
        ),
        migrations.CreateModel(
            name='EventResource',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=255)),
                ('resource_type', models.CharField(choices=[('PRESENTATION', 'Presentation'), ('DOCUMENT', 'Document'), ('VIDEO', 'Video'), ('AUDIO', 'Audio'), ('IMAGE', 'Image'), ('OTHER', 'Other')], max_length=20)),
                ('file', models.FileField(upload_to='event_resources/')),
                ('url', models.URLField(blank=True, null=True)),
                ('description', models.TextField(blank=True)),
                ('is_public', models.BooleanField(default=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resources', to='events.event')),
                ('uploaded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='RecurringEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recurrence_type', models.CharField(choices=[('DAILY', 'Daily'), ('WEEKLY', 'Weekly'), ('BIWEEKLY', 'Bi-weekly'), ('MONTHLY', 'Monthly')], max_length=10)),
                ('recurrence_end_date', models.DateField(blank=True, null=True)),
                ('event', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='recurrence', to='events.event')),
            ],
        ),
        migrations.CreateModel(
            name='EventFeedback',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('rating', models.PositiveIntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])),
                ('comments', models.TextField(blank=True)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feedbacks', to='events.event')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('event', 'user')},
            },
        ),
        migrations.CreateModel(
            name='EventRegistration',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('registration_date', models.DateTimeField(auto_now_add=True)),
                ('attendance_status', models.CharField(choices=[('REGISTERED', 'Registered'), ('ATTENDED', 'Attended'), ('ABSENT', 'Absent'), ('EXCUSED', 'Excused')], default='REGISTERED', max_length=10)),
                ('attendance_marked_at', models.DateTimeField(blank=True, null=True)),
                ('cancellation_date', models.DateTimeField(blank=True, null=True)),
                ('attendance_marked_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='marked_attendances', to=settings.AUTH_USER_MODEL)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registrations', to='events.event')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_registrations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('event', 'user')},
            },
        ),
    ]
