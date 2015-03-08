from django.conf.urls import patterns, include, url
from immunization_schedule import views

urlpatterns = patterns('',
                       url(r'^authorize/$', views.authorize_handler, name='authorize'),
                       url(r'^authorize/retrieve_tokens/', views.retrieve_tokens, name='retrieve'),
                       url(r'^list_patients/', views.list_patients, name='list_patients'),
                       url(r'^$', 'immunization_schedule.views.home', name='home'),
                       url(r'^patient_vaccinations/', include('patient_vaccinations.urls')))
