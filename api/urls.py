from django.urls import path, include

from . import views

urlpatterns = [
    path('create_scorm_course/', views.create_scorm_course, name='create_scorm_course'),
    path('register/', views.register_for_course, name='register_and_create_scorm_registration'),
    path('scorm_cloud_operations/', views.scorm_cloud_operations, name='scorm_cloud_operations'),
    path('delete_course/<str:course_id>/', views.DeleteCourseView.as_view(), name='delete_course'),
]
