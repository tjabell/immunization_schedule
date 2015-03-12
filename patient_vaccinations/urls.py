from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r'(\d+)/$',
                           'patient_vaccinations.views.index',
                           name='index'),
                       url(r'vaccinate/',
                           'patient_vaccinations.views.vaccinate',
                           name='vaccinate'))
