from django.urls import path, include

from . import administrator_views, facilitator_views, learner_views, supervisor_views, auth_views
from django.views.i18n import set_language

urlpatterns = [
     # Authentication views
     path('login/', auth_views.LoginView.as_view(), name='login'),
     path('signup/', auth_views.SignupView.as_view(), name='signup'),
     path('logout/', auth_views.user_logout, name='logout'),

     # Administrator views
     path('administrator/dashboard/', administrator_views.AdministratorDashboardView.as_view(), name='administrator_dashboard'),   
     path('administrator/calendar/', administrator_views.AdministratorCalendarView.as_view(), name='administrator_calendar'),
     path('administrator/leaderboard/', administrator_views.AdministratorLeaderboardView.as_view(), name='administrator_leaderboard'),

     path('administrator/course/create/', administrator_views.AdministratorCourseCreateView.as_view(), name='administrator_create_course'),
     path('administrator/course/list/', administrator_views.AdministratorCourseListView.as_view(), name='administrator_course_list'),
     path('administrator/course/<uuid:pk>/', administrator_views.AdministratorCourseDetailView.as_view(), name='administrator_course_detail'),
     path('administrator/course/<uuid:pk>/edit/', administrator_views.AdministratorCourseEditView.as_view(), name='administrator_course_edit'),
     path('administrator/course/<uuid:pk>/publish/', administrator_views.AdministratorCoursePublishView.as_view(), name='administrator_course_publish'),
     path('administrator/course/<uuid:pk>/unpublish/', administrator_views.AdministratorCourseUnpublishView.as_view(), name='administrator_course_unpublish'),
     path('administrator/course/<uuid:pk>/delete/', administrator_views.AdministratorCourseDeleteView.as_view(), name='administrator_course_delete'),

     path('administrator/course/categories/', administrator_views.AdministratorCourseCategoryListView.as_view(), name='administrator_course_category_list'),
     path('administrator/course/learning_paths/', administrator_views.AdministratorLearningPathListView.as_view(), name='administrator_learning_path_list'),


     path('administrator/course/<uuid:course_id>/resources/', administrator_views.AdministratorLearningResourcesListView.as_view(), name='administrator_course_resource_list'),
     path('administrator/course/<uuid:course_id>/resources/create/', administrator_views.AdministratorLearningResourceCreateView.as_view(), name='administrator_learning_resource_create'),
     path('administrator/course/<uuid:course_id>/learning-resources/<uuid:resource_id>/edit/', 
          administrator_views.AdministratorLearningResourceEditView.as_view(), 
          name='administrator_learning_resource_edit'),
     path('administrator/course/<uuid:course_id>/learning-resources/<uuid:resource_id>/delete/', 
          administrator_views.AdministratorLearningResourceDeleteView.as_view(), 
          name='administrator_learning_resource_delete'),
     path('administrator/course/<uuid:course_id>/learning-resource/<uuid:pk>/', administrator_views.AdministratorLearningResourceDetailView.as_view(), name='administrator_learning_resource_detail'),
     path('administrator/scorm-upload/', administrator_views.scorm_upload_view, name='administrator_scorm_upload'),

     path('administrator/course/<uuid:course_id>/resource/<uuid:resource_id>/quiz/create/', administrator_views.QuizCreateView.as_view(), name='administrator_quiz_create'),
     path('administrator/course/<uuid:course_id>/resource/<uuid:resource_id>/quiz/<uuid:quiz_id>/add-questions/', administrator_views.QuizAddQuestionsView.as_view(), name='administrator_quiz_add_questions'),
     path('administrator/courses/<uuid:course_id>/resources/<uuid:resource_id>/quiz/edit/', 
         administrator_views.QuizEditView.as_view(), 
         name='administrator_quiz_edit'),


     path('administrator/deliveries/', administrator_views.AdministratorDeliveryListView.as_view(), name='administrator_delivery_list'),
     path('administrator/delivery/create/', administrator_views.AdministratorDeliveryCreateView.as_view(), name='administrator_delivery_create'),
     path('administrator/deliveries/<uuid:pk>/', administrator_views.AdministratorDeliveryDetailView.as_view(), name='administrator_delivery_detail'),
     path('administrator/delivery/<uuid:pk>/edit/', administrator_views.AdministratorDeliveryEditView.as_view(), name='administrator_delivery_edit'),
     path('administrator/delivery/<uuid:pk>/delete/', administrator_views.AdministratorDeliveryDeleteView.as_view(), name='administrator_delivery_delete'),


     path('administrator/enrollments/', administrator_views.AdministratorEnrollmentListView.as_view(), name='administrator_enrollment_list'),
     path('administrator/enrollment/create/', administrator_views.AdministratorEnrollmentCreateView.as_view(), name='administrator_enrollment_create'),
     path('administrator/enrollments/<uuid:pk>/edit/', administrator_views.AdministratorEnrollmentEditView.as_view(), name='administrator_enrollment_edit'),
     path('administrator/enrollments/<uuid:pk>/delete/', administrator_views.AdministratorEnrollmentDeleteView.as_view(), name='administrator_enrollment_delete'),


     path('administrator/deliveries/<uuid:delivery_id>/add-course-component/', administrator_views.CourseComponentCreateView.as_view(), name='administrator_add_course_component'),
    path('administrator/components/<uuid:parent_component_id>/add-resource-component/', administrator_views.ResourceComponentCreateView.as_view(), name='administrator_add_resource_component'),
    path('administrator/deliveries/<uuid:delivery_id>/add-resource-component/', 
     administrator_views.ResourceComponentCreateView.as_view(), 
     name='administrator_add_resource_component_to_course'),

     path('administrator/delivery-component/<uuid:pk>/edit/', administrator_views.AdministratorDeliveryComponentEditView.as_view(), name='administrator_delivery_component_edit'),
     path('administrator/delivery-component/<uuid:pk>/delete/', administrator_views.AdministratorDeliveryComponentDeleteView.as_view(), name='administrator_delivery_component_delete'),



     path('administrator/program/list/', administrator_views.AdministratorProgramListView.as_view(), name='administrator_program_list'),
     path('administrator/program/<uuid:pk>/', administrator_views.AdministratorProgramDetailView.as_view(), name='administrator_program_detail'),
     path('administrator/program/create/', administrator_views.AdministratorProgramCreateView.as_view(), name='administrator_program_create'),
     path('administrator/program/<uuid:pk>/delete/', administrator_views.AdministratorProgramDeleteView.as_view(), name='administrator_program_delete'),
     path('administrator/programs/<uuid:pk>/edit/', administrator_views.AdministratorProgramEditView.as_view(), name='administrator_program_edit'),
     path('administrator/program/<uuid:pk>/publish/', administrator_views.AdministratorProgramPublishView.as_view(), name='administrator_program_publish'),
     path('administrator/program/<uuid:pk>/unpublish/', administrator_views.AdministratorProgramUnpublishView.as_view(), name='administrator_program_unpublish'),
     path('administrator/program/<uuid:program_id>/add-course/', administrator_views.AdministratorProgramCourseCreateView.as_view(), name='administrator_program_add_course'),



     path('administrator/report/course_completion/', administrator_views.AdministratorCourseCompletionReportView.as_view(), name='administrator_course_completion_report'),
     path('administrator/report/user_progress/', administrator_views.AdministratorUserProgressReportView.as_view(), name='administrator_user_progress_report'),
     path('administrator/report/assessment_results/', administrator_views.AdministratorAssessmentResultsReportView.as_view(), name='administrator_assessment_results_report'),
     path('administrator/report/user_engagement/', administrator_views.AdministratorUserEngagementReportView.as_view(), name='administrator_user_engagement_report'),
     path('administrator/report/resource_usage/', administrator_views.AdministratorResourceUsageReportView.as_view(), name='administrator_resource_usage_report'),
     path('administrator/report/certification_tracking/', administrator_views.AdministratorCertificationTrackingReportView.as_view(), name='administrator_certification_tracking_report'),
     path('administrator/report/learner_feedback/', administrator_views.AdministratorLearnerFeedbackReportView.as_view(), name='administrator_learner_feedback_report'),
     path('administrator/report/custom_report/', administrator_views.AdministratorCustomReportView.as_view(), name='administrator_custom_report'),

     path('administrator/learners/', administrator_views.AdministratorLearnerListView.as_view(), name='administrator_learner_list'),
     path('administrator/facilitators/', administrator_views.AdministratorFacilitatorListView.as_view(), name='administrator_facilitator_list'),
     path('administrator/supervisors/', administrator_views.AdministratorSupervisorListView.as_view(), name='administrator_supervisor_list'),

     path('administrator/certificates/', administrator_views.AdministratorCertificateListView.as_view(), name='administrator_certificate_list'),

    # announcements
     path('administrator/announcements/', administrator_views.AdministratorAnnouncementListView.as_view(), name='administrator_announcement_list'),
     path('administrator/announcement/create/', administrator_views.AdministratorAnnouncementCreateView.as_view(), name='administrator_announcement_create'),
     path('administrator/announcement/<uuid:pk>/detail/', administrator_views.AdministratorAnnouncementDetailView.as_view(), name='administrator_announcement_detail'),  










     path('administrator/help-support/', administrator_views.AdministratorHelpSupportView.as_view(), name='administrator_help_support'),
     path('administrator/messages/', administrator_views.AdministratorMessageListView.as_view(), name='administrator_message_list'),
     path('administrator/settings/', administrator_views.AdministratorSettingsView.as_view(), name='administrator_settings'),


     path('administrator/course/enrollments/', administrator_views.AdministratorEnrollmentListView.as_view(), name='administrator_course_enrollment_list'),


     path('administrator/notification/', administrator_views.AdministratorNotificationListView.as_view(), name='administrator_notification_list'),

     # ================================================================
     #                           Learner URLs
     # ================================================================

     # Dashboard 
     path('learner/dashboard/', learner_views.DashboardView.as_view(), name='learner_dashboard'),

     # Programs
     path('learner/programs/', learner_views.ProgramListView.as_view(), name='learner_program_list'),
     path('learner/programs/<uuid:pk>/', learner_views.ProgramDetailView.as_view(), name='learner_program_detail'),
     path('learner/my-programs/', learner_views.MyProgramListView.as_view(), name='learner_my_programs'),
     path('learner/my-programs/<uuid:enrollment_id>/', learner_views.MyProgramDetailView.as_view(), name='learner_my_program_detail'),
    
     # Courses
     path('learner/courses/', learner_views.CourseListView.as_view(), name='learner_course_list'),
     path('learner/courses/<uuid:pk>/', learner_views.CourseDetailView.as_view(), name='learner_course_detail'),
     path('learner/my-courses/', learner_views.MyCourseListView.as_view(), name='learner_my_courses'),
     path('learner/my-courses/<uuid:enrollment_id>/', learner_views.MyCourseDetailView.as_view(), name='learner_my_course_detail'),

     path('learner/my-programs/<uuid:enrollment_id>/course/<uuid:course_id>/direct/', 
         learner_views.DirectCourseConsumptionView.as_view(), 
         name='direct_course_consumption'),
     path('learner/my-programs/<uuid:enrollment_id>/resource/<uuid:resource_id>/direct/', 
         learner_views.DirectResourceConsumptionView.as_view(), 
         name='direct_resource_consumption'),

     path('learner/my-programs/<uuid:enrollment_id>/delivery/course/<uuid:component_id>/', learner_views.DeliveryCourseConsumptionView.as_view(), name='delivery_course_consumption'),
     path('learner/my-programs/<uuid:enrollment_id>/delivery/resource/<uuid:component_id>/', learner_views.DeliveryResourceConsumptionView.as_view(), name='delivery_resource_consumption'),


     path('learner/resource/<uuid:resource_id>/', learner_views.LearningResourceDetailView.as_view(), name='learning_resource_detail'),

     # Enrollment
     path('learner/enroll/<str:enrollment_type>/<uuid:object_id>/', learner_views.EnrollmentConfirmationView.as_view(), name='learner_enroll'),

     path('learner/calendar/', learner_views.CalendarView.as_view(), name='learner_calendar'),
     path('learner/messages/', learner_views.MessageListView.as_view(), name='learner_message_list'),
     path('learner/assignments/', learner_views.AssigmentListView.as_view(), name='learner_assignment_list'),
     path('learner/grades/', learner_views.GradesView.as_view(), name='learner_grades'),
     path('learner/resources/', learner_views.ResourceView.as_view(), name='learner_resource_list'),
     path('learner/progress/', learner_views.ProgressView.as_view(), name='learner_progress'),
     path('learner/forum/', learner_views.ForumView.as_view(), name='learner_forum'),
     path('learner/certificates/', learner_views.CertificateView.as_view(), name='learner_certificate'),
     path('learner/badges/', learner_views.BadgeView.as_view(), name='learner_badge'),
     path('learner/leaderboard/', learner_views.LeaderboardView.as_view(), name='learner_leaderboard'),
     path('learner/profile/', learner_views.ProfileView.as_view(), name='learner_profile'),
     path('learner/settings/', learner_views.SettingsView.as_view(), name='learner_settings'),
     path('learner/help-support/', learner_views.HelpSupportView.as_view(), name='learner_help_support'),

     path('learner/notification/', learner_views.NotificationListView.as_view(), name='learner_notification_list'),

     # Facilitator views
     path('facilitator/dashboard/', facilitator_views.FacilitatorDashboardView.as_view(), name='facilitator_dashboard'),
     path('facilitator/notification/', facilitator_views.FacilitatorNotificationListView.as_view(), name='facilitator_notification_list'),

     # Supervisor views
     path('supervisor/dashboard/', supervisor_views.SupervisorDashboardView.as_view(), name='supervisor_dashboard'),
     path('supervisor/notification/', supervisor_views.SupervisorNotificationListView.as_view(), name='supervisor_notification_list'),
]
