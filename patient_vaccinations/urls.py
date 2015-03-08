from django.conf.urls import patterns, url

urlpatterns = patterns('',
                       url(r'(\d+)/$',
                           'patient_vaccinations.views.index',
                           name='index'),)
