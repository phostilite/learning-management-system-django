from django.urls import path, include

from . import administartor_views, facilitator_views, learner_views, auth_views

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
    path('administrator/course/list/', administartor_views.list_courses, name='course_list'),
    path('administrator/course/<uuid:pk>/', administartor_views.CourseDetailView.as_view(), name='course_detail'),

    path('administrator/learners/', administartor_views.AdministratorLearnerListView.as_view(), name='administrator_learner_list'),
    path('administrator/facilitators/', administartor_views.AdministratorFacilitatorListView.as_view(), name='administrator_facilitator_list'),
    path('administrator/supervisors/', administartor_views.AdministratorSupervisorListView.as_view(), name='administrator_supervisor_list'),

    # Learner views
    path('learner/dashboard/', learner_views.LearnerDashboardView.as_view(), name='learner_dashboard'),

    # Facilitator views
    path('facilitator/dashboard/', facilitator_views.FacilitatorDashboardView.as_view(), name='facilitator_dashboard'),
]
