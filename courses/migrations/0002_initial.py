# Generated by Django 5.1.1 on 2024-09-19 05:57

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('courses', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_courses', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='course',
            name='prerequisites',
            field=models.ManyToManyField(blank=True, related_name='required_for', to='courses.course'),
        ),
        migrations.AddField(
            model_name='coursecategory',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='courses.coursecategory'),
        ),
        migrations.AddField(
            model_name='course',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='courses.coursecategory'),
        ),
        migrations.AddField(
            model_name='delivery',
            name='course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='deliveries', to='courses.course'),
        ),
        migrations.AddField(
            model_name='deliverycomponent',
            name='delivery',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='components', to='courses.delivery'),
        ),
        migrations.AddField(
            model_name='deliverycomponent',
            name='parent_component',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='child_components', to='courses.deliverycomponent'),
        ),
        migrations.AddField(
            model_name='componentcompletion',
            name='delivery_component',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='courses.deliverycomponent'),
        ),
        migrations.AddField(
            model_name='enrollment',
            name='course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='direct_enrollments', to='courses.course'),
        ),
        migrations.AddField(
            model_name='enrollment',
            name='delivery',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='courses.delivery'),
        ),
        migrations.AddField(
            model_name='enrollment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='componentcompletion',
            name='enrollment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='component_completions', to='courses.enrollment'),
        ),
        migrations.AddField(
            model_name='learningresource',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resources', to='courses.course'),
        ),
        migrations.AddField(
            model_name='deliverycomponent',
            name='learning_resource',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='courses.learningresource'),
        ),
        migrations.AddField(
            model_name='componentcompletion',
            name='learning_resource',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='courses.learningresource'),
        ),
        migrations.AddField(
            model_name='program',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_programs', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='program',
            name='prerequisites',
            field=models.ManyToManyField(blank=True, related_name='required_for', to='courses.program'),
        ),
        migrations.AddField(
            model_name='enrollment',
            name='program',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='direct_enrollments', to='courses.program'),
        ),
        migrations.AddField(
            model_name='delivery',
            name='program',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='deliveries', to='courses.program'),
        ),
        migrations.AddField(
            model_name='programcourse',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='courses.course'),
        ),
        migrations.AddField(
            model_name='programcourse',
            name='program',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='program_courses', to='courses.program'),
        ),
        migrations.AddField(
            model_name='deliverycomponent',
            name='program_course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='courses.programcourse'),
        ),
        migrations.AddField(
            model_name='componentcompletion',
            name='program_course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='courses.programcourse'),
        ),
        migrations.AddField(
            model_name='progress',
            name='course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='courses.course'),
        ),
        migrations.AddField(
            model_name='progress',
            name='enrollment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress_records', to='courses.enrollment'),
        ),
        migrations.AddField(
            model_name='progress',
            name='learning_resource',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='courses.learningresource'),
        ),
        migrations.AddField(
            model_name='progress',
            name='program',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='courses.program'),
        ),
        migrations.AddField(
            model_name='recommendation',
            name='course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='course_recommendations', to='courses.course'),
        ),
        migrations.AddField(
            model_name='recommendation',
            name='learning_resource',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='resource_recommendations', to='courses.learningresource'),
        ),
        migrations.AddField(
            model_name='recommendation',
            name='program',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='program_recommendations', to='courses.program'),
        ),
        migrations.AddField(
            model_name='recommendation',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recommendations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='review',
            name='content_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
        ),
        migrations.AddField(
            model_name='review',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='scormregistration',
            name='enrollment',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='scorm_registration', to='courses.enrollment'),
        ),
        migrations.AddField(
            model_name='scormresource',
            name='learning_resource',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='scorm_details', to='courses.learningresource'),
        ),
        migrations.AddField(
            model_name='program',
            name='tags',
            field=models.ManyToManyField(blank=True, to='courses.tag'),
        ),
        migrations.AddField(
            model_name='course',
            name='tags',
            field=models.ManyToManyField(blank=True, to='courses.tag'),
        ),
        migrations.AlterUniqueTogether(
            name='enrollment',
            unique_together={('user', 'course'), ('user', 'delivery'), ('user', 'program')},
        ),
        migrations.AlterUniqueTogether(
            name='programcourse',
            unique_together={('program', 'course')},
        ),
        migrations.AlterUniqueTogether(
            name='deliverycomponent',
            unique_together={('delivery', 'learning_resource'), ('delivery', 'program_course')},
        ),
        migrations.AlterUniqueTogether(
            name='componentcompletion',
            unique_together={('enrollment', 'delivery_component'), ('enrollment', 'learning_resource'), ('enrollment', 'program_course')},
        ),
        migrations.AlterUniqueTogether(
            name='progress',
            unique_together={('enrollment', 'course'), ('enrollment', 'learning_resource'), ('enrollment', 'program')},
        ),
        migrations.AddIndex(
            model_name='recommendation',
            index=models.Index(fields=['user', 'recommendation_type', 'score'], name='courses_rec_user_id_cc175d_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='recommendation',
            unique_together={('user', 'recommendation_type', 'course', 'program', 'learning_resource')},
        ),
        migrations.AddIndex(
            model_name='review',
            index=models.Index(fields=['content_type', 'object_id'], name='courses_rev_content_c8af84_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='review',
            unique_together={('user', 'content_type', 'object_id')},
        ),
    ]
