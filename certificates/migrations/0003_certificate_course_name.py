# Generated by Django 5.0.6 on 2024-08-29 12:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0002_certificate_certificate_image_certificate_timestamp_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificate',
            name='course_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
