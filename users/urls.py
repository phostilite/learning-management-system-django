from django.urls import path, include

from . import administartor_views, facilitator_views, learner_views, supervisor_views, auth_views
from django.views.i18n import set_language

urlpatterns = [
    # Authentication views
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('signup/', auth_views.SignupView.as_view(), name='signup'),
    path('logout/', auth_views.user_logout, name='logout'),

    # Administrator views
    path('administrator/dashboard/', administartor_views.AdministratorDashboardView.as_view(), name='administrator_dashboard'),   
    path('administrator/calendar/', administartor_views.AdministratorCalendarView.as_view(), name='administrator_calendar'),
    path('administrator/leaderboard/', administartor_views.AdministratorLeaderboardView.as_view(), name='administrator_leaderboard'),
    
    path('administrator/course/create/', administartor_views.AdministratorCourseCreateView.as_view(), name='administrator_create_course'),
    path('administrator/course/list/', administartor_views.AdministratorCourseListView.as_view(), name='administrator_course_list'),
    path('administrator/course/<uuid:pk>/', administartor_views.AdministratorCourseDetailView.as_view(), name='administrator_course_detail'),
    path('administrator/course/<uuid:pk>/edit/', administartor_views.AdministratorCourseEditView.as_view(), name='administrator_course_edit'),
    path('administrator/course/<uuid:pk>/publish/', administartor_views.AdministratorCoursePublishView.as_view(), name='administrator_course_publish'),
    path('administrator/course/<uuid:pk>/unpublish/', administartor_views.AdministratorCourseUnpublishView.as_view(), name='administrator_course_unpublish'),
    path('administrator/course/<uuid:pk>/delete/', administartor_views.AdministratorCourseDeleteView.as_view(), name='administrator_course_delete'),
    
    path('administrator/course/categories/', administartor_views.AdministratorCourseCategoryListView.as_view(), name='administrator_course_category_list'),
    path('administrator/course/learning_paths/', administartor_views.AdministratorLearningPathListView.as_view(), name='administrator_learning_path_list'),


    path('administrator/course/<uuid:course_id>/resources/', administartor_views.AdministratorLearningResourcesListView.as_view(), name='administrator_course_resource_list'),
    path('administrator/course/<uuid:course_id>/resources/create/', administartor_views.AdministratorLearningResourceCreateView.as_view(), name='administrator_learning_resource_create'),
    path('administrator/course/<uuid:course_id>/learning-resources/<uuid:resource_id>/edit/', 
         administartor_views.AdministratorLearningResourceEditView.as_view(), 
         name='administrator_learning_resource_edit'),
    path('administrator/course/<uuid:course_id>/learning-resources/<uuid:resource_id>/delete/', 
         administartor_views.AdministratorLearningResourceDeleteView.as_view(), 
         name='administrator_learning_resource_delete'),
    path('administrator/course/<uuid:course_id>/learning-resource/<uuid:pk>/', administartor_views.AdministratorLearningResourceDetailView.as_view(), name='administrator_learning_resource_detail'),
    path('administrator/scorm-upload/', administartor_views.scorm_upload_view, name='administrator_scorm_upload'),

    path('administrator/deliveries/', administartor_views.AdministratorDeliveryListView.as_view(), name='administrator_delivery_list'),
    path('administrator/delivery/create/', administartor_views.AdministratorDeliveryCreateView.as_view(), name='administrator_delivery_create'),
    path('administrator/deliveries/<uuid:pk>/', administartor_views.AdministratorDeliveryDetailView.as_view(), name='administrator_delivery_detail'),
    path('administrator/delivery/<uuid:pk>/edit/', administartor_views.AdministratorDeliveryEditView.as_view(), name='administrator_delivery_edit'),
    path('administrator/delivery/<uuid:pk>/delete/', administartor_views.AdministratorDeliveryDeleteView.as_view(), name='administrator_delivery_delete'),


    path('administrator/enrollments/', administartor_views.AdministratorEnrollmentListView.as_view(), name='administrator_enrollment_list'),
    path('administrator/enrollment/create/', administartor_views.AdministratorEnrollmentCreateView.as_view(), name='administrator_enrollment_create'),
    path('administrator/enrollments/<uuid:pk>/edit/', administartor_views.AdministratorEnrollmentEditView.as_view(), name='administrator_enrollment_edit'),
    path('administrator/enrollments/<uuid:pk>/delete/', administartor_views.AdministratorEnrollmentDeleteView.as_view(), name='administrator_enrollment_delete'),


    path('administrator/deliveries/components/create/', administartor_views.AdministratorDeliveryComponentCreateView.as_view(), name='administrator_delivery_component_create'),
    path('administrator/delivery-component/<uuid:pk>/edit/', administartor_views.AdministratorDeliveryComponentEditView.as_view(), name='administrator_delivery_component_edit'),
    path('administrator/delivery-component/<uuid:pk>/delete/', administartor_views.AdministratorDeliveryComponentDeleteView.as_view(), name='administrator_delivery_component_delete'),
    
    path('administrator/program/list/', administartor_views.AdministratorProgramListView.as_view(), name='administrator_program_list'),
    path('administrator/program/<uuid:pk>/', administartor_views.AdministratorProgramDetailView.as_view(), name='administrator_program_detail'),
    path('administrator/program/create/', administartor_views.AdministratorProgramCreateView.as_view(), name='administrator_program_create'),
    path('administrator/program/<uuid:pk>/delete/', administartor_views.AdministratorProgramDeleteView.as_view(), name='administrator_program_delete'),
    path('administrator/programs/<uuid:pk>/edit/', administartor_views.AdministratorProgramEditView.as_view(), name='administrator_program_edit'),
    path('administrator/program/<uuid:pk>/publish/', administartor_views.AdministratorProgramPublishView.as_view(), name='administrator_program_publish'),
    path('administrator/program/<uuid:pk>/unpublish/', administartor_views.AdministratorProgramUnpublishView.as_view(), name='administrator_program_unpublish'),
    path('administrator/program/<uuid:program_id>/add-course/', administartor_views.AdministratorProgramCourseCreateView.as_view(), name='administrator_program_add_course'),



    path('administrator/report/course_completion/', administartor_views.AdministratorCourseCompletionReportView.as_view(), name='administrator_course_completion_report'),
    path('administrator/report/user_progress/', administartor_views.AdministratorUserProgressReportView.as_view(), name='administrator_user_progress_report'),
    path('administrator/report/assessment_results/', administartor_views.AdministratorAssessmentResultsReportView.as_view(), name='administrator_assessment_results_report'),
    path('administrator/report/user_engagement/', administartor_views.AdministratorUserEngagementReportView.as_view(), name='administrator_user_engagement_report'),
    path('administrator/report/resource_usage/', administartor_views.AdministratorResourceUsageReportView.as_view(), name='administrator_resource_usage_report'),
    path('administrator/report/certification_tracking/', administartor_views.AdministratorCertificationTrackingReportView.as_view(), name='administrator_certification_tracking_report'),
    path('administrator/report/learner_feedback/', administartor_views.AdministratorLearnerFeedbackReportView.as_view(), name='administrator_learner_feedback_report'),
    path('administrator/report/custom_report/', administartor_views.AdministratorCustomReportView.as_view(), name='administrator_custom_report'),

    path('administrator/learners/', administartor_views.AdministratorLearnerListView.as_view(), name='administrator_learner_list'),
    path('administrator/facilitators/', administartor_views.AdministratorFacilitatorListView.as_view(), name='administrator_facilitator_list'),
    path('administrator/supervisors/', administartor_views.AdministratorSupervisorListView.as_view(), name='administrator_supervisor_list'),

    path('administrator/certificates/', administartor_views.AdministratorCertificateListView.as_view(), name='administrator_certificate_list'),

    path('administrator/announcements/', administartor_views.AdministratorAnnouncementListView.as_view(), name='administrator_announcement_list'),
    path('administrator/help-support/', administartor_views.AdministratorHelpSupportView.as_view(), name='administrator_help_support'),
    path('administrator/messages/', administartor_views.AdministratorMessageListView.as_view(), name='administrator_message_list'),
    path('administrator/settings/', administartor_views.AdministratorSettingsView.as_view(), name='administrator_settings'),


    path('administrator/course/enrollments/', administartor_views.AdministratorEnrollmentListView.as_view(), name='administrator_course_enrollment_list'),


    path('administrator/notification/', administartor_views.AdministratorNotificationListView.as_view(), name='administrator_notification_list'),

    # Learner views
    path('learner/dashboard/', learner_views.LearnerDashboardView.as_view(), name='learner_dashboard'),
    path('learner/my-courses/', learner_views.LearnerMyCoursesView.as_view(), name='learner_my_courses'),
    path('learner/course/detail/<uuid:course_id>/', learner_views.LearnerCourseDetailView.as_view(), name='learner_administrator_course_detail'),
    path('learner/calendar/', learner_views.LearnerCalendarView.as_view(), name='learner_calendar'),
    path('learner/messages/', learner_views.LearnerMessageListView.as_view(), name='learner_message_list'),
    path('learner/assignments/', learner_views.LearnerAssigmentListView.as_view(), name='learner_assignment_list'),
    path('learner/grades/', learner_views.LearnerGradesView.as_view(), name='learner_grades'),
    path('learner/resources/', learner_views.LearnerResourceView.as_view(), name='learner_resource_list'),
    path('learner/progress/', learner_views.LearnerProgressView.as_view(), name='learner_progress'),
    path('learner/forum/', learner_views.LearnerForumView.as_view(), name='learner_forum'),
    path('learner/certificates/', learner_views.LearnerCertificateView.as_view(), name='learner_certificate'),
    path('learner/badges/', learner_views.LearnerBadgeView.as_view(), name='learner_badge'),
    path('learner/leaderboard/', learner_views.LearnerLeaderboardView.as_view(), name='learner_leaderboard'),
    path('learner/profile/', learner_views.LearnerProfileView.as_view(), name='learner_profile'),
    path('learner/settings/', learner_views.LearnerSettingsView.as_view(), name='learner_settings'),
    path('learner/help-support/', learner_views.LearnerHelpSupportView.as_view(), name='learner_help_support'),

    path('learner/course/library/', learner_views.LearnerCourseLibraryView.as_view(), name='learner_course_library'),

    path('learner/programs/', learner_views.LearnerProgramCatalogView.as_view(), name='learner_programs'),
    path('learner/courses/<uuid:course_id>/details/', learner_views.administrator_course_details, name='administrator_course_details_api'),

    path('learner/notification/', learner_views.LearnerNotificationListView.as_view(), name='learner_notification_list'),

    # Facilitator views
    path('facilitator/dashboard/', facilitator_views.FacilitatorDashboardView.as_view(), name='facilitator_dashboard'),
    path('facilitator/notification/', facilitator_views.FacilitatorNotificationListView.as_view(), name='facilitator_notification_list'),

    # Supervisor views
    path('supervisor/dashboard/', supervisor_views.SupervisorDashboardView.as_view(), name='supervisor_dashboard'),
    path('supervisor/notification/', supervisor_views.SupervisorNotificationListView.as_view(), name='supervisor_notification_list'),
]
