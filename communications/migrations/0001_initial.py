# Generated by Django 5.1.1 on 2024-09-24 06:15

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
            name='Thread',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('subject', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Draft',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('subject', models.CharField(blank=True, max_length=255)),
                ('content', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('recipients', models.ManyToManyField(related_name='draft_recipients', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='message_drafts', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Label',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('color', models.CharField(default='#FFFFFF', max_length=7)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='message_labels', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'name')},
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('object_id', models.UUIDField(blank=True, null=True)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contenttypes.contenttype')),
                ('sender', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_messages', to=settings.AUTH_USER_MODEL)),
                ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='communications.thread')),
            ],
        ),
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('file', models.FileField(upload_to='message_attachments/')),
                ('filename', models.CharField(max_length=255)),
                ('file_size', models.PositiveIntegerField()),
                ('content_type', models.CharField(max_length=100)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='communications.message')),
            ],
        ),
        migrations.CreateModel(
            name='UserMessageSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_notifications', models.BooleanField(default=True)),
                ('messages_per_page', models.PositiveIntegerField(default=50)),
                ('signature', models.TextField(blank=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='message_settings', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Recipient',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_read', models.BooleanField(default=False)),
                ('is_archived', models.BooleanField(default=False)),
                ('is_starred', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_threads', to=settings.AUTH_USER_MODEL)),
                ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipients', to='communications.thread')),
            ],
            options={
                'unique_together': {('thread', 'user')},
            },
        ),
        migrations.CreateModel(
            name='ThreadLabel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('label', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='threads', to='communications.label')),
                ('thread', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='labels', to='communications.thread')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='thread_labels', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('thread', 'label', 'user')},
            },
        ),
    ]