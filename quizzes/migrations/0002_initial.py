# Generated by Django 5.1.1 on 2024-09-30 18:15

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('quizzes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='quizattempt',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='quiz_attempts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='quizresponse',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='quizzes.question'),
        ),
        migrations.AddField(
            model_name='quizresponse',
            name='quiz_attempt',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='quizzes.quizattempt'),
        ),
        migrations.AddField(
            model_name='quizresponse',
            name='selected_choice',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='quizzes.choice'),
        ),
    ]
