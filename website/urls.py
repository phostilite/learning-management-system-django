from django.urls import path, include
from django.views.i18n import set_language
from . import views

urlpatterns = [
    # path('', views.landing_page, name='landing_page'),
    path('', views.marketing_page, name='marketing_page'),
    path('about/', views.about_page, name='about_page'),
    path('contact/', views.contact_page, name='contact_page'),
]
