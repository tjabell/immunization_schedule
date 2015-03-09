from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from patient_vaccinations.models import get_vaccinations, Patient
import urllib
import requests

base_url = 'https://drchrono.com'

months = ['Birth',
          '1 month',
          '2 months',
          '4 months',
          '6 months',
          '12 months',
          '15 months',
          '18 months',
          '24 months',
          '4-6 years',
          '11-12 years',
          '14-18 years']

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

# vaccine : (vaccine_id, [(dose_map_key, month, consecutive_months_for_dose)]
immunization_schedule = {
    'Hepatitis B': (1, [('first', 'Birth', 2),  ('second', '1 month', 2), ('third', '6 months', 4), ('c', '11-12 years', 1)]),
    'Diptheria, Tetanus, Pertussis': (2, [('first','2 months', 1), ('second', '4 months', 1), ('third', '6 months', 1), ('fourth', '15 months', 2)]),
    'H.Influenzae type B': (4, [('first','2 months', 1), ('second', '4 months', 1), ('third', '6 months', 1), ('fourth', '12 months', 2)]),
    'Inactivated Polio': (5, [('first','2 months', 1), ('second', '4 months', 1), ('third', '6 months', 4), ('fourth', '4-6 years', 1)]),
    'Pneumococcal Conjugate': (6, [('first','2 months', 1), ('second', '4 months', 1), ('third', '6 months', 1), ('fourth', '12 months', 2)]),
    'Measles, Mumps, Rubella': (3, [('first', '12 months', 2), ('second', '4-6 years', 1), ('c', '11-12 years', 1)]),
    'Varicella (Chickenpox)': (7, [('first', '12 months', 3), ('c', '11-12 years', 1)]),
    'Hepatitis A': (8, [('first', '24 months',  4)])}


class VaccinationMonth(object):
    def __init__(self, name, dose, dose_due, dose_key):
        self.name = name
        self.dose = dose
        self.dose_due = dose_due
        self.dose_key = dose_key
        self.consecutive_months = 0


class PatientVaccination(object):
    def __init__(self, name, is_overdue, months):
        self.name = name
        self.is_overdue = is_overdue
        self.months = months


class PatientVaccinationsSchedule(object):
    """Patient Vaccinations Schedule"""
    def __init__(self, patient, months, vaccinations):
        self.patient = patient
        self.months = months
        self.vaccinations = vaccinations


def index(request,  id):
    access_token = request.session.get('access_token')

    if access_token is None:
        return HttpResponseRedirect(reverse('authorize'))

    authorization_header = "Bearer %s" % urllib.quote(access_token)
    headers = {'Authorization': authorization_header}
    patient_url = '/api/patients/%s' % id
    patient_response = requests.get(base_url + patient_url, headers=headers).json()

    patient = Patient(
        id,
        patient_response['first_name'] + ' ' + patient_response['last_name'],
        patient_response['date_of_birth'])
    patient.vaccinations = get_vaccinations(patient.id)

    vaccinations = []
    for immunization_key in sorted(immunization_schedule):
        is_overdue = False
        vaccination_months = []
        immunization = immunization_schedule[immunization_key]
        id, schedule = immunization

        # horrible hack to skip months that are consecutive in the schedule
        skip = 0
        for monthnum in months:
            vm = VaccinationMonth(monthnum, None, False, '')

            for dose_key, dose_month, consecutive_months in schedule:
                if monthnum == dose_month:
                    vm.dose_key = dose_key
                    vm.dose_due = True
                    vm.dose = dose_map[dose_key]
                    vm.consecutive_months = consecutive_months
                    skip = consecutive_months
                    vaccination_months.append(vm)

            if skip == 0:
                vaccination_months.append(vm)
            else:
                skip -= 1

        vaccinations.append(
            PatientVaccination(immunization_key,
                               is_overdue,
                               vaccination_months))

    context = {'patient_vaccinations':
               PatientVaccinationsSchedule(patient, months, vaccinations)}

    return render(request, 'patient_schedule.html', context)
