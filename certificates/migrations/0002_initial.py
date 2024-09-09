# Generated by Django 5.1.1 on 2024-09-08 12:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('certificates', '0001_initial'),
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificate',
            name='course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='certificates', to='courses.course'),
        ),
        migrations.AddField(
            model_name='certificate',
            name='course_delivery',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='certificates', to='courses.delivery'),
        ),
        migrations.AddField(
            model_name='certificate',
            name='enrollment',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='certificate', to='courses.enrollment'),
        ),
    ]
