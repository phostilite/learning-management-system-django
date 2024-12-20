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
        path('<uuid:pk>/delete/', administrator_views.CourseDeleteView.as_view(), name='administrator_course_delete'),
        path('categories/', administrator_views.AdministratorCourseCategoryListView.as_view(), name='administrator_course_category_list'),
        path('learning_paths/', administrator_views.AdministratorLearningPathListView.as_view(), name='administrator_learning_path_list'),
        path('<uuid:course_id>/deliveries/', administrator_views.CourseDeliveryListView.as_view(), name='administrator_course_delivery_list'),
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
    path('administrator/deliveries/', administrator_views.AdministratorDeliveryListView.as_view(), name='administrator_delivery_list'),

    path('administrator/deliveries/create/basic-info/', administrator_views.AdministratorDeliveryCreateView.as_view(), name='administrator_delivery_create'),
    path('administrator/deliveries/<uuid:pk>/create/enrollment/', administrator_views.DeliveryEnrollmentsFormView.as_view(), name='administrator_delivery_enrollment_form'),
    path('administrator/deliveries/<uuid:pk>/create/component/', administrator_views.DeliveryComponentFormView.as_view(), name='administrator_delivery_component_form'),
    path('administrator/deliveries/<uuid:pk>/create/email-templates/', administrator_views.DeliveryEmailTemplateView.as_view(), name='administrator_delivery_email_templates'),


    path('administrator/deliveries/<uuid:pk>/', administrator_views.AdministratorDeliveryDetailView.as_view(), name='administrator_delivery_detail'),
    path('administrator/deliveries/<uuid:pk>/edit/', administrator_views.AdministratorDeliveryEditView.as_view(), name='administrator_delivery_edit'),
    path('administrator/deliveries/<uuid:pk>/delete/', administrator_views.AdministratorDeliveryDeleteView.as_view(), name='administrator_delivery_delete'),

    path('administrator/delivery/<uuid:pk>/enrollments/', administrator_views.DeliveryEnrollmentListView.as_view(), name='administrator_delivery_enrollments'),
    path('administrator/delivery/<uuid:pk>/enrollments/create/', administrator_views.DeliveryEnrollmentsCreateView.as_view(), name='administrator_delivery_enrollments_create'),

    # Delivery Course Components
    path('administrator/deliveries/<uuid:pk>/add-course-component/', administrator_views.DeliveryCourseComponentCreateView.as_view(), name='administrator_add_delivery_course_component'),

    # Delivery Resource Components
    path('administrator/components/<uuid:parent_component_id>/add-resource-component/', administrator_views.ResourceComponentCreateView.as_view(), name='administrator_add_resource_component'),

    # Delivery Add Resource To Course
    path('administrator/deliveries/<uuid:delivery_id>/add-resource-component/', administrator_views.ResourceComponentCreateView.as_view(), name='administrator_add_resource_component_to_course'),
    
    # Delivery Component Edit
    path('administrator/delivery-component/<uuid:pk>/edit/', administrator_views.AdministratorDeliveryComponentEditView.as_view(), name='administrator_delivery_component_edit'),

    # Delivery Component Delete
    path('administrator/delivery-component/<uuid:pk>/delete/', administrator_views.AdministratorDeliveryComponentDeleteView.as_view(), name='administrator_delivery_component_delete'),

    # Program Management
    path('administrator/program/', include([
        path('list/', administrator_views.AdministratorProgramListView.as_view(), name='administrator_program_list'),
        path('<uuid:pk>/', administrator_views.AdministratorProgramDetailView.as_view(), name='administrator_program_detail'),
        path('create/', administrator_views.AdministratorProgramCreateView.as_view(), name='administrator_program_create'),
        path('<uuid:pk>/delete/', administrator_views.AdministratorProgramDeleteView.as_view(), name='administrator_program_delete'),
        path('<uuid:pk>/edit/', administrator_views.AdministratorProgramEditView.as_view(), name='administrator_program_edit'),
        path('<uuid:pk>/publish/', administrator_views.AdministratorProgramPublishView.as_view(), name='administrator_program_publish'),
        path('<uuid:pk>/unpublish/', administrator_views.AdministratorProgramUnpublishView.as_view(), name='administrator_program_unpublish'),
        path('<uuid:program_id>/courses/', administrator_views.AdministratorProgramCoursesView.as_view(), name='administrator_program_courses'),
        path('<uuid:program_id>/add-course/', administrator_views.AdministratorProgramCourseCreateView.as_view(), name='administrator_program_add_course'),
        path('<uuid:program_id>/remove-course/<uuid:program_course_id>/', administrator_views.AdministratorProgramCourseRemoveView.as_view(), name='administrator_program_remove_course'),
        path('<uuid:program_id>/deliveries/', administrator_views.ProgramDeliveryListView.as_view(), name='administrator_program_delivery_list'),
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
    path('administrator/messages/', administrator_views.AdministratorMessageListView.as_view(), name='administrator_message_list'),
    path('administrator/settings/', administrator_views.AdministratorSettingsView.as_view(), name='administrator_settings'),

    # Help and Support Management
    path('administrator/help-support/', administrator_views.AdministratorHelpSupportView.as_view(), name='administrator_help_support'),
    path('administrator/help-support/tickets/create/',administrator_views.AdministratorTicketCreateView.as_view(), name='administrator_tickets_create'),
    path('administrator/help-support/tickets/<uuid:pk>/detail/', administrator_views.AdministratorTicketDetailView.as_view(), name='administrator_tickets_detail'),
    path('administrator/help-support/tickets/<uuid:pk>/edit/', administrator_views.AdministratorTicketEditView.as_view(), name= 'administrator_ticket_edit'),
    path('administrator/help-support/tickets/<uuid:pk>/delete/', administrator_views.AdministratorTicketDeleteView.as_view(), name= 'administrator_ticket_delete'),
    path('administrator/help-support/faq/create/', administrator_views.AdministratorFaqCreateView.as_view(), name='administrator_faq_create'),
    path('administrator/help-support/faq/<uuid:pk>/edit/', administrator_views.AdministratorFaqEditView.as_view(), name='administrator_faq_edit'),
    path('administrator/help-support/faq/<uuid:pk>/delete/', administrator_views.AdministratorFaqDeleteView.as_view(), name='administrator_faq_delete'),
    
    path('administrator/help-support/support_category/', administrator_views.AdministratorSupportCategoryView.as_view(), name='administrator_support_category'),
    path('administrator/help-support/category/<uuid:pk>/edit/', administrator_views.AdministratorCategoryEditView.as_view(), name='administrator_category_edit'),
    path('administrator/help-support/category/<uuid:pk>/delete/', administrator_views.AdministratorCategoryDeleteView.as_view(), name='administrator_category_delete'),
    
    path('administrator/messages/', administrator_views.AdministratorMessageListView.as_view(), name='administrator_message_list'),
    path('administrator/settings/', administrator_views.AdministratorSettingsView.as_view(), name='administrator_settings'),

    # Announcements
    path('administrator/announcements/', administrator_views.AdministratorAnnouncementListView.as_view(), name='administrator_announcement_list'),
    path('administrator/announcement/<uuid:pk>/detail/', administrator_views.AdministratorAnnouncementDetailView.as_view(), name='administrator_announcement_detail'),
    path('administrator/announcement/<uuid:pk>/delete/', administrator_views.AdministratorAnnouncementDeleteView.as_view(), name='administrator_announcement_delete'),
    path('administrator/announcement/<uuid:pk>/update/', administrator_views.AdministratorAnnouncementUpdateView.as_view(), name='administrator_announcement_update'),
    path('administrator/announcement/<uuid:pk>/manage_recipient/', administrator_views.AdministratorAnnouncementManageRecipientView.as_view(), name='administrator_announcement_manage_recipients'),
    path('administrator/announcement/filter-users/<uuid:announcement_id>/<uuid:announcement_recipient_id>/', administrator_views.FilterUsersByRecipientTypeView.as_view(), name='filter_users_by_recipient_type'),

    # Notification Views
    path('administrator/notifications/recent/', administrator_views.RecentNotificationsView.as_view(), name='administrator_recent_notifications'),
    path('administrator/notification/', administrator_views.NotificationListView.as_view(), name='administrator_notification_list'),
    path('administrator/notifications/<uuid:pk>/mark-read/', administrator_views.MarkNotificationReadView.as_view(), name='administrator_mark_notification_read'),
    path('administrator/notifications/mark-all-read/', administrator_views.MarkAllNotificationsReadView.as_view(), name='administrator_mark_all_notifications_read'),
    path('administrator/notifications/unread-count/', administrator_views.UnreadNotificationsCountView.as_view(), name='administrator_unread_notifications_count'),

    # ==================== Learner URLs ====================

    # Dashboard and General Views
    path('learner/dashboard/', learner_views.DashboardView.as_view(), name='learner_dashboard'),

    path('learner/learning-catalog/', learner_views.LearningCatalogView.as_view(), name='learner_learning_catalog'),
    path('learner/programs/', learner_views.ProgramListView.as_view(), name='learner_program_list'),
    path('learner/course/<uuid:pk>/', learner_views.CourseDetailView.as_view(), name='learner_course_detail'),
    path('learner/program/<uuid:pk>/', learner_views.ProgramDetailView.as_view(), name='learner_program_detail'),

    path('learner/enroll/', learner_views.EnrollmentCreateView.as_view(), name='learner_enrollment_create'),
    path('learner/enrollments/', learner_views.EnrollmentsView.as_view(), name='learner_enrollments'),
    path('learner/enrollments/course-consumption/<uuid:enrollment_id>/', learner_views.CourseConsumptionView.as_view(), name='learner_course_consumption'),


    path('learner/progress/', learner_views.ProgressView.as_view(), name='learner_progress'),

    path('learner/calendar/', learner_views.CalendarView.as_view(), name='learner_calendar'),
    path('learner/messages/', learner_views.MessageListView.as_view(), name='learner_message_list'),
    path('learner/resources/', learner_views.ResourceView.as_view(), name='learner_resource_list'),
    path('learner/leaderboard/', learner_views.LeaderboardView.as_view(), name='learner_leaderboard'),
    path('learner/settings/', learner_views.SettingsView.as_view(), name='learner_settings'),
    
    path('learner/help-support/', learner_views.HelpSupportView.as_view(), name='learner_help_support'),
    path('learner/help-support/tickets/create/',learner_views.LearnerTicketCreateView.as_view(), name='learner_tickets_create'),
    path('learner/help-support/tickets/<uuid:pk>/ticket_details/', learner_views.LearnerTicketDetailView.as_view(), name='learner_tickets_detail'),

    path('learner/announcements/', learner_views.AnnouncementListView.as_view(), name='learner_announcements'),
    path('learner/announcement/<uuid:pk>/detail/', learner_views.AnnouncementDetailView.as_view(), name='learner_announcement_detail'),
    path('learner/announcement/<uuid:pk>/mark-read/', learner_views.AnnouncementReadView.as_view(), name='learner_mark_announcement_read'),

    path('learner/notifications/recent/', learner_views.RecentNotificationsView.as_view(), name='learner_recent_notifications'),
    path('learner/notification/', learner_views.NotificationListView.as_view(), name='learner_notifications'),
    path('learner/notifications/<uuid:pk>/mark-read/', learner_views.MarkNotificationReadView.as_view(), name='learner_mark_notification_read'),
    path('learner/notifications/mark-all-read/', learner_views.MarkAllNotificationsReadView.as_view(), name='learner_mark_all_notifications_read'),
    path('learner/notifications/unread-count/', learner_views.UnreadNotificationsCountView.as_view(), name='learner_unread_notifications_count'),

    # ==================== Facilitator URLs ====================
    path('facilitator/dashboard/', facilitator_views.FacilitatorDashboardView.as_view(), name='facilitator_dashboard'),
    path('facilitator/notification/', facilitator_views.FacilitatorNotificationListView.as_view(), name='facilitator_notification_list'),

    # ==================== Supervisor URLs ====================
    path('supervisor/dashboard/', supervisor_views.SupervisorDashboardView.as_view(), name='supervisor_dashboard'),
    path('supervisor/notification/', supervisor_views.SupervisorNotificationListView.as_view(), name='supervisor_notification_list'),
]