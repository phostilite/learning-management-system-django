# Generated by Django 5.1.1 on 2024-09-30 12:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('announcements', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='publish_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='announcementrecipient',
            name='recipient_type',
            field=models.CharField(choices=[('ALL', 'All Users'), ('LEARNER', 'All Learners'), ('FACILITATOR', 'All Faciltators'), ('SUPERVISOR', 'All Supervisors'), ('USER', 'Specific User')], max_length=20),
        ),
    ]
