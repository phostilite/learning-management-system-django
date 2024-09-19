# Generated by Django 5.1.1 on 2024-09-10 13:59

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_alter_learningresource_resource_type'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Recommendation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recommendation_type', models.CharField(choices=[('COURSE', 'Course'), ('PROGRAM', 'Program'), ('LEARNING_RESOURCE', 'Learning Resource')], max_length=20)),
                ('score', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(1.0)])),
                ('reason', models.TextField(blank=True, help_text='Explanation for this recommendation')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='course_recommendations', to='courses.course')),
                ('learning_resource', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='resource_recommendations', to='courses.learningresource')),
                ('program', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='program_recommendations', to='courses.program')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommendations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'indexes': [models.Index(fields=['user', 'recommendation_type', 'score'], name='courses_rec_user_id_cc175d_idx')],
                'unique_together': {('user', 'recommendation_type', 'course', 'program', 'learning_resource')},
            },
        ),
    ]