from django.urls import path, include
from django.views.i18n import set_language
from . import administrator_views, facilitator_views, learner_views, supervisor_views, auth_views, general_views, password_reset_views

urlpatterns = [
    # ==================== Authentication URLs ====================
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('signup/', auth_views.SignupView.as_view(), name='signup'),
    path('logout/', auth_views.user_logout, name='logout'),

    # ==================== Password Reset URLs ====================
    path('password-reset/', password_reset_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', password_reset_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', 
     password_reset_views.PasswordResetConfirmView.as_view(), 
     name='password_reset_confirm'),
    path('password-reset/complete/', password_reset_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # ==================== General URLs ============================
    path('session-expired/', general_views.SessionExpiredView.as_view(), name='session_expired'),

    # ==================== Administrator URLs ====================
    # Dashboard and General Views
    path('administrator/dashboard/', administrator_views.AdministratorDashboardView.as_view(), name='administrator_dashboard'),
    path('administrator/calendar/', administrator_views.AdministratorCalendarView.as_view(), name='administrator_calendar'),
    path('administrator/leaderboard/', administrator_views.AdministratorLeaderboardView.as_view(), name='administrator_leaderboard'),

    # Course Management
    path('administrator/course/', include([
        path('create/', administrator_views.AdministratorCourseCreateView.as_view(), name='administrator_create_course'),
        path('list/', administrator_views.AdministratorCourseListView.as_view(), name='administrator_course_list'),
        path('<uuid:pk>/', administrator_views.AdministratorCourseDetailView.as_view(), name='administrator_course_detail'),
        path('<uuid:pk>/edit/', administrator_views.AdministratorCourseEditView.as_view(), name='administrator_course_edit'),
        path('<uuid:pk>/publish/', administrator_views.AdministratorCoursePublishView.as_view(), name='administrator_course_publish'),
        path('<uuid:pk>/unpublish/', administrator_views.AdministratorCourseUnpublishView.as_view(), name='administrator_course_unpublish'),
        path('<uuid:pk>/delete/', administrator_views.AdministratorCourseDeleteView.as_view(), name='administrator_course_delete'),
        path('categories/', administrator_views.AdministratorCourseCategoryListView.as_view(), name='administrator_course_category_list'),
        path('learning_paths/', administrator_views.AdministratorLearningPathListView.as_view(), name='administrator_learning_path_list'),
    ])),

    # Learning Resources
    path('administrator/course/<uuid:course_id>/resources/', include([
        path('', administrator_views.AdministratorLearningResourcesListView.as_view(), name='administrator_course_resource_list'),
        path('create/', administrator_views.AdministratorLearningResourceCreateView.as_view(), name='administrator_learning_resource_create'),
        path('<uuid:resource_id>/edit/', administrator_views.AdministratorLearningResourceEditView.as_view(), name='administrator_learning_resource_edit'),
        path('<uuid:resource_id>/delete/', administrator_views.AdministratorLearningResourceDeleteView.as_view(), name='administrator_learning_resource_delete'),
        path('<uuid:pk>/', administrator_views.AdministratorLearningResourceDetailView.as_view(), name='administrator_learning_resource_detail'),
    ])),
    path('administrator/scorm-upload/', administrator_views.scorm_upload_view, name='administrator_scorm_upload'),

    # Quiz Management
    path('administrator/course/<uuid:course_id>/resource/<uuid:resource_id>/quiz/', include([
        path('create/', administrator_views.QuizCreateView.as_view(), name='administrator_quiz_create'),
        path('<uuid:quiz_id>/add-questions/', administrator_views.QuizAddQuestionsView.as_view(), name='administrator_quiz_add_questions'),
        path('edit/', administrator_views.QuizEditView.as_view(), name='administrator_quiz_edit'),
    ])),

    # Delivery Management
    path('administrator/deliveries/', include([
        path('', administrator_views.AdministratorDeliveryListView.as_view(), name='administrator_delivery_list'),
        path('create/', administrator_views.AdministratorDeliveryCreateView.as_view(), name='administrator_delivery_create'),
        path('<uuid:pk>/', administrator_views.AdministratorDeliveryDetailView.as_view(), name='administrator_delivery_detail'),
        path('<uuid:pk>/edit/', administrator_views.AdministratorDeliveryEditView.as_view(), name='administrator_delivery_edit'),
        path('<uuid:pk>/delete/', administrator_views.AdministratorDeliveryDeleteView.as_view(), name='administrator_delivery_delete'),
    ])),

    # Enrollment Management
    path('administrator/enrollments/', include([
        path('', administrator_views.AdministratorEnrollmentListView.as_view(), name='administrator_enrollment_list'),
        path('create/', administrator_views.AdministratorEnrollmentCreateView.as_view(), name='administrator_enrollment_create'),
        path('<uuid:pk>/edit/', administrator_views.AdministratorEnrollmentEditView.as_view(), name='administrator_enrollment_edit'),
        path('<uuid:pk>/delete/', administrator_views.AdministratorEnrollmentDeleteView.as_view(), name='administrator_enrollment_delete'),
    ])),

    # Delivery Components
    path('administrator/deliveries/<uuid:delivery_id>/add-course-component/', administrator_views.CourseComponentCreateView.as_view(), name='administrator_add_course_component'),
    path('administrator/components/<uuid:parent_component_id>/add-resource-component/', administrator_views.ResourceComponentCreateView.as_view(), name='administrator_add_resource_component'),
    path('administrator/deliveries/<uuid:delivery_id>/add-resource-component/', administrator_views.ResourceComponentCreateView.as_view(), name='administrator_add_resource_component_to_course'),
    path('administrator/delivery-component/<uuid:pk>/edit/', administrator_views.AdministratorDeliveryComponentEditView.as_view(), name='administrator_delivery_component_edit'),
    path('administrator/delivery-component/<uuid:pk>/delete/', administrator_views.AdministratorDeliveryComponentDeleteView.as_view(), name='administrator_delivery_component_delete'),

    path('administrator/delivery/<uuid:delivery_id>/enrollments/', administrator_views.DeliveryEnrollmentListView.as_view(), name='administrator_delivery_enrollments'),
    path('administrator/delivery/<uuid:delivery_id>/enrollments/create/', administrator_views.DeliveryEnrollmentsCreateView.as_view(), name='administrator_delivery_enrollments_create'),

    # Program Management
    path('administrator/program/', include([
        path('list/', administrator_views.AdministratorProgramListView.as_view(), name='administrator_program_list'),
        path('<uuid:pk>/', administrator_views.AdministratorProgramDetailView.as_view(), name='administrator_program_detail'),
        path('create/', administrator_views.AdministratorProgramCreateView.as_view(), name='administrator_program_create'),
        path('<uuid:pk>/delete/', administrator_views.AdministratorProgramDeleteView.as_view(), name='administrator_program_delete'),
        path('<uuid:pk>/edit/', administrator_views.AdministratorProgramEditView.as_view(), name='administrator_program_edit'),
        path('<uuid:pk>/publish/', administrator_views.AdministratorProgramPublishView.as_view(), name='administrator_program_publish'),
        path('<uuid:pk>/unpublish/', administrator_views.AdministratorProgramUnpublishView.as_view(), name='administrator_program_unpublish'),
        path('<uuid:program_id>/add-course/', administrator_views.AdministratorProgramCourseCreateView.as_view(), name='administrator_program_add_course'),
    ])),

    # Reports
    path('administrator/report/', include([
        path('course_completion/', administrator_views.AdministratorCourseCompletionReportView.as_view(), name='administrator_course_completion_report'),
        path('user_progress/', administrator_views.AdministratorUserProgressReportView.as_view(), name='administrator_user_progress_report'),
        path('assessment_results/', administrator_views.AdministratorAssessmentResultsReportView.as_view(), name='administrator_assessment_results_report'),
        path('user_engagement/', administrator_views.AdministratorUserEngagementReportView.as_view(), name='administrator_user_engagement_report'),
        path('resource_usage/', administrator_views.AdministratorResourceUsageReportView.as_view(), name='administrator_resource_usage_report'),
        path('certification_tracking/', administrator_views.AdministratorCertificationTrackingReportView.as_view(), name='administrator_certification_tracking_report'),
        path('learner_feedback/', administrator_views.AdministratorLearnerFeedbackReportView.as_view(), name='administrator_learner_feedback_report'),
        path('custom_report/', administrator_views.AdministratorCustomReportView.as_view(), name='administrator_custom_report'),
    ])),

    # User Management
    path('administrator/learners/', administrator_views.AdministratorLearnerListView.as_view(), name='administrator_learner_list'),
    path('administrator/facilitators/', administrator_views.AdministratorFacilitatorListView.as_view(), name='administrator_facilitator_list'),
    path('administrator/supervisors/', administrator_views.AdministratorSupervisorListView.as_view(), name='administrator_supervisor_list'),
    
    path('administrator/organization/', administrator_views.OrganizationDetailsView.as_view(), name='administrator_organization_details'),
    path('administrator/organization/units/', administrator_views.OrganizationUnitsView.as_view(), name='administrator_organization_units'),
    path('administrator/organization/groups/', administrator_views.OrganizationGroupsView.as_view(), name='administrator_organization_groups'),
    path('administrator/organization/locations/', administrator_views.OrganizationLocationsView.as_view(), name='administrator_organization_locations'),
    path('administrator/organization/job-positions/', administrator_views.OrganizationJobPositionsView.as_view(), name='administrator_organization_job_positions'),
    path('administrator/organization/employee-profiles/', administrator_views.OrganizationEmployeeProfilesView.as_view(), name='administrator_organization_employee_profiles'),

    path('administrator/organization/add-employee/', administrator_views.AddEmployeeView.as_view(), name='administrator_add_employee'),
    path('administrator/organization/add-job-position/', administrator_views.AddJobPositionView.as_view(), name='administrator_add_job_position'),
    path('administrator/organization/add-location/', administrator_views.AddLocationView.as_view(), name='administrator_add_location'),
    path('administrator/organization/add-unit/', administrator_views.AddOrganizationUnitView.as_view(), name='administrator_add_unit'),
    path('administrator/organization/add-group/', administrator_views.AddOrganizationGroupView.as_view(), name='administrator_add_group'),

    # Other Administrator Views
    path('administrator/certificates/', administrator_views.AdministratorCertificateListView.as_view(), name='administrator_certificate_list'),
    path('administrator/announcements/', administrator_views.AdministratorAnnouncementListView.as_view(), name='administrator_announcement_list'),
    path('administrator/help-support/', administrator_views.AdministratorHelpSupportView.as_view(), name='administrator_help_support'),
    path('administrator/messages/', administrator_views.AdministratorMessageListView.as_view(), name='administrator_message_list'),
    path('administrator/settings/', administrator_views.AdministratorSettingsView.as_view(), name='administrator_settings'),

    # Notification Views
    path('administrator/notifications/recent/', administrator_views.RecentNotificationsView.as_view(), name='administrator_recent_notifications'),
    path('administrator/notification/', administrator_views.NotificationListView.as_view(), name='administrator_notification_list'),
    path('administrator/notifications/<uuid:pk>/mark-read/', administrator_views.MarkNotificationReadView.as_view(), name='administrator_mark_notification_read'),
    path('administrator/notifications/mark-all-read/', administrator_views.MarkAllNotificationsReadView.as_view(), name='administrator_mark_all_notifications_read'),
    path('administrator/notifications/unread-count/', administrator_views.UnreadNotificationsCountView.as_view(), name='administrator_unread_notifications_count'),

    # ==================== Learner URLs ====================
    # Dashboard and General Views
    path('learner/dashboard/', learner_views.DashboardView.as_view(), name='learner_dashboard'),
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
    path('learner/settings/', learner_views.SettingsView.as_view(), name='learner_settings'),
    path('learner/help-support/', learner_views.HelpSupportView.as_view(), name='learner_help_support'),

    path('learner/notifications/recent/', learner_views.RecentNotificationsView.as_view(), name='learner_recent_notifications'),
    path('learner/notification/', learner_views.NotificationListView.as_view(), name='learner_notification_list'),
    path('learner/notifications/<uuid:pk>/mark-read/', learner_views.MarkNotificationReadView.as_view(), name='learner_mark_notification_read'),
    path('learner/notifications/mark-all-read/', learner_views.MarkAllNotificationsReadView.as_view(), name='learner_mark_all_notifications_read'),
    path('learner/notifications/unread-count/', learner_views.UnreadNotificationsCountView.as_view(), name='learner_unread_notifications_count'),

    # Programs
    path('learner/programs/', include([
        path('', learner_views.ProgramListView.as_view(), name='learner_program_list'),
        path('<uuid:pk>/', learner_views.ProgramDetailView.as_view(), name='learner_program_detail'),
        path('my-programs/', learner_views.MyProgramListView.as_view(), name='learner_my_programs'),
        path('my-programs/<uuid:enrollment_id>/', learner_views.MyProgramDetailView.as_view(), name='learner_my_program_detail'),
    ])),

    # Courses
    path('learner/courses/', include([
        path('', learner_views.CourseListView.as_view(), name='learner_course_list'),
        path('<uuid:pk>/', learner_views.CourseDetailView.as_view(), name='learner_course_detail'),
        path('my-courses/', learner_views.MyCourseListView.as_view(), name='learner_my_courses'),
        path('my-courses/<uuid:enrollment_id>/', learner_views.MyCourseDetailView.as_view(), name='learner_my_course_detail'),
    ])),

    # Direct Consumption
    path('learner/my-programs/<uuid:enrollment_id>/course/<uuid:course_id>/direct/', 
         learner_views.DirectCourseConsumptionView.as_view(), 
         name='direct_course_consumption'),
    path('learner/my-programs/<uuid:enrollment_id>/resource/<uuid:resource_id>/direct/', 
         learner_views.DirectResourceConsumptionView.as_view(), 
         name='direct_resource_consumption'),

    # Delivery Consumption
    path('learner/my-programs/<uuid:enrollment_id>/delivery/course/<uuid:component_id>/', 
         learner_views.DeliveryCourseConsumptionView.as_view(), 
         name='delivery_course_consumption'),
    path('learner/my-programs/<uuid:enrollment_id>/delivery/resource/<uuid:component_id>/', 
         learner_views.DeliveryResourceConsumptionView.as_view(), 
         name='delivery_resource_consumption'),

    # Learning Resources
    path('learner/resource/<uuid:resource_id>/', learner_views.LearningResourceDetailView.as_view(), name='learning_resource_detail'),

    # Enrollment
    path('learner/enroll/<str:enrollment_type>/<uuid:object_id>/', learner_views.EnrollmentConfirmationView.as_view(), name='learner_enroll'),

    # ==================== Facilitator URLs ====================
    path('facilitator/dashboard/', facilitator_views.FacilitatorDashboardView.as_view(), name='facilitator_dashboard'),
    path('facilitator/notification/', facilitator_views.FacilitatorNotificationListView.as_view(), name='facilitator_notification_list'),

    # ==================== Supervisor URLs ====================
    path('supervisor/dashboard/', supervisor_views.SupervisorDashboardView.as_view(), name='supervisor_dashboard'),
    path('supervisor/notification/', supervisor_views.SupervisorNotificationListView.as_view(), name='supervisor_notification_list'),
]