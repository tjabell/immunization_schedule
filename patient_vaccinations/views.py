from __future__ import print_function
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from patient_vaccinations.models import Patient
import urllib
import requests


base_url = 'https://drchrono.com'

view_months = [
    ('Birth', 0),
    ('1 month', 1),
    ('2 months', 2),
    ('4 months', 4),
    ('6 months', 6),
    ('12 months', 12),
    ('15 months', 15),
    ('18 months', 18),
    ('24 months', 24),
    ('4-6 years', 48),
    ('11-12 years', 132),
    ('14-18 years', 164)]

dose_map = {
    'first': '1st Dose',
    'second': '2nd Dose',
    'third': '3rd Dose',
    'fourth': '4th Dose',
    'fifth': '5th Dose',
    'c': 'catch up',
    't': 'Tetanus + Diptheria',
    's': '1 dose (in selected areas)'
}

patient_vaccinations = {}


def index(request,  id):
    access_token = request.session.get('access_token')

    if access_token is None:
        return HttpResponseRedirect(reverse('authorize'))

    authorization_header = "Bearer %s" % urllib.quote(access_token)
    headers = {'Authorization': authorization_header}
    patient_url = '/api/patients/%s' % id
    patient_response = requests.get(
        base_url + patient_url, headers=headers).json()

    patient = Patient(
        id,
        patient_response['first_name'] + ' ' + patient_response['last_name'],
        patient_response['date_of_birth'])

    id = int(id)
    if id not in patient_vaccinations:
        patient_vaccinations[id] = set()

    pvs = patient_vaccinations[id]
    pv = {}
    for i in pvs:
        pv[i] = True

    context = {
        'patient': patient,
        'pv': pv}

    return render(request, 'patient_schedule.html', context)


def vaccinate(request):
    patient_id = int(request.POST["patient_id"])
    pv = request.POST["vaccinated_ids"]

    if patient_id not in patient_vaccinations:
        patient_vaccinations[patient_id] = set()

    [patient_vaccinations[patient_id].add(v) for v in pv.split('#')]
    return HttpResponseRedirect(
        reverse('index', args=[int(patient_id)]))
