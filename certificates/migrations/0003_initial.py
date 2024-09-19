# Generated by Django 5.1.1 on 2024-09-19 05:57

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('certificates', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='certificate',
            name='revoked_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='revoked_certificates', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='certificate',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='certificates', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='certificateissuancelog',
            name='certificate',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='issuance_logs', to='certificates.certificate'),
        ),
        migrations.AddField(
            model_name='certificateissuancelog',
            name='issued_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='certificate',
            name='certificate_template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='certificates.certificatetemplate'),
        ),
        migrations.AddIndex(
            model_name='certificate',
            index=models.Index(fields=['certificate_number'], name='certificate_certifi_cd0c46_idx'),
        ),
        migrations.AddIndex(
            model_name='certificate',
            index=models.Index(fields=['issue_date'], name='certificate_issue_d_e50978_idx'),
        ),
        migrations.AddIndex(
            model_name='certificate',
            index=models.Index(fields=['user', 'course'], name='certificate_user_id_2a7ce8_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='certificate',
            unique_together={('user', 'course', 'course_delivery')},
        ),
    ]
