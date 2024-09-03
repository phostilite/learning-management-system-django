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
    path('administrator/course/create/', administartor_views.create_course, name='create_course'),
    path('administrator/course/list/', administartor_views.CourseListView.as_view(), name='course_list'),
    path('administrator/course/<uuid:pk>/', administartor_views.CourseDetailView.as_view(), name='course_detail'),
    path('administrator/course/categories/', administartor_views.AdministratorCourseCategoryListView.as_view(), name='administrator_course_category_list'),
    path('administrator/course/learning_paths/', administartor_views.AdministratorLearningPathListView.as_view(), name='administrator_learning_path_list'),
    path('administrator/course/<uuid:course_id>/add-resource/', administartor_views.add_learning_resource, name='add_learning_resource'),


    path('administrator/course/<uuid:course_id>/resources/', administartor_views.AdministratorLearningResourcesListView.as_view(), name='administrator_course_resource_list'),
    path('administrator/course/<uuid:course_id>/resources/create/', administartor_views.AdministratorLearningResourceCreateView.as_view(), name='administrator_course_resource_create'),

    path('administrator/course/<uuid:course_id>/deliveries/', administartor_views.AdministratorCourseDeliveryListView.as_view(), name='administrator_course_delivery_list'),
    path('administrator/course/<uuid:course_id>/delivery/create/', administartor_views.AdministratorCourseDeliveryCreateView.as_view(), name='administrator_course_delivery_create'),
    path('administrator/course/<uuid:course_id>/delivery/<uuid:delivery_id>/', administartor_views.AdministratorCourseDeliveryDetailView.as_view(), name='administrator_course_delivery_detail'),
    path('administrator/course/<uuid:course_id>/delivery/<uuid:delivery_id>/enroll/', 
         administartor_views.AdministratorCourseDeliveryEnrollView.as_view(), 
         name='administrator_course_delivery_enroll'),


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
    path('administrator/course/<uuid:course_id>/delete/', administartor_views.AdministratorCourseDeleteView.as_view(), name='administrator_delete_course'),


    path('administrator/course/enrollments/', administartor_views.AdministratorEnrollmentListView.as_view(), name='administrator_course_enrollment_list'),

    # Learner views
    path('learner/dashboard/', learner_views.LearnerDashboardView.as_view(), name='learner_dashboard'),
    path('learner/my-courses/', learner_views.LearnerMyCoursesView.as_view(), name='learner_my_courses'),
    path('learner/course/detail/<uuid:course_id>/', learner_views.LearnerCourseDetailView.as_view(), name='learner_course_detail'),
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

    # Facilitator views
    path('facilitator/dashboard/', facilitator_views.FacilitatorDashboardView.as_view(), name='facilitator_dashboard'),

    # Supervisor views
    path('supervisor/dashboard/', supervisor_views.SupervisorDashboardView.as_view(), name='supervisor_dashboard'),
]
