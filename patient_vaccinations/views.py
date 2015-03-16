from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from patient_vaccinations.models import get_vaccinations, Patient
import urllib
import requests
import json

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

# vaccine :
# (vaccine_id, [(dose_map_key, month, consecutive_months_for_dose, can_be_given_in_range, (ordinal_range_start, ordinal_range_end))]
# child_immunization_schedule = {
#     'Hepatitis B': (1, [('first', 'Birth', 2, (0,2)),  ('second', '1 month', 2, (1, ,2)), ('third', '6 months', 4, (6, 24)), ('c', '11-12 years', 1, (132,144))]),
#     'Diptheria, Tetanus, Pertussis': (2, [('first','2 months', 1), ('second', '4 months', 1), ('third', '6 months', 1), ('fourth', '15 months', 2)]),
#     'H.Influenzae type B': (4, [('first','2 months', 1), ('second', '4 months', 1), ('third', '6 months', 1), ('fourth', '12 months', 2)]),
#     'Inactivated Polio': (5, [('first','2 months', 1), ('second', '4 months', 1), ('third', '6 months', 4), ('fourth', '4-6 years', 1)]),
#     'Pneumococcal Conjugate': (6, [('first','2 months', 1), ('second', '4 months', 1), ('third', '6 months', 1), ('fourth', '12 months', 2)]),
#     'Measles, Mumps, Rubella': (3, [('first', '12 months', 2), ('second', '4-6 years', 1), ('c', '11-12 years', 1)]),
#     'Varicella (Chickenpox)': (7, [('first', '12 months', 3), ('c', '11-12 years', 1)]),
#     'Hepatitis A': (8, [('first', '24 months',  4)])}

# vaccine :
# (vaccine_id, [(dose_map_key, month, consecutive_months_for_dose, can_be_given_in_range, (ordinal_range_start, ordinal_range_end))]
child_immunization_schedule = {
    'Hepatitis B': (1, [('first', 'Birth', 2, (0, 2)),  ('second', '1 month', 2, (1, 2)), ('third', '6 months', 4, (6, 24)), ('c', '11-12 years', 1, (132, 144))])
}


class OrdinalRange(object):
    """Represents an ordered range [0,1,2...]
    """
    def __init__(self, start, end):
        super(OrdinalRange, self).__init__()
        self.start = start
        self.end = end

    def overlaps(self, ordinal_range):
        return self.start >= ordinal_range.end

    def overlapped(self, ordinal_range):
        return self.end <= ordinal_range.start


class Immunization(object):
    """Immunization information
    """
    def __init__(self, dose_map_key, age_can_be_taken,
                 consecutive_months, ordinal_range):
        super(Immunization, self).__init__()
        self.dose_map_key = dose_map_key
        self.age_can_be_taken = age_can_be_taken
        self.consecutive_months = consecutive_months
        self.ordinal_range = OrdinalRange(*ordinal_range)

    def __str__(self):
        return "{Immunization: " + self.dose_map_key + "}"

    def __repr__(self):
        return self.__str__()


def has_overlap(immunization, immunization_schedule):
    return any(
        [immunization.ordinal_range.overlaps(
            immunization_sched_month.ordinal_range)
         and immunization.dose_map_key != immunization_sched_month.dose_map_key
         for immunization_sched_month in immunization_schedule])


def has_overlapped(immunization, immunization_schedule):
        return any(
            [immunization.ordinal_range.overlapped(
                immunization_sched_month.ordinal_range)
             and immunization.dose_map_key
             != immunization_sched_month.dose_map_key
             for immunization_sched_month in immunization_schedule])


class VaccinationMonth(object):
    def __init__(self, name, dose, dose_due, dose_key):
        self.scheduleId = 0
        self.name = name
        self.dose = dose
        self.dose_due = dose_due
        self.dose_key = dose_key
        self.consecutive_months = 0


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
    patient_response = requests.get(
        base_url + patient_url, headers=headers).json()

    patient = Patient(
        id,
        patient_response['first_name'] + ' ' + patient_response['last_name'],
        patient_response['date_of_birth'])
    patient.vaccinations = get_vaccinations(patient.id)

    vaccinations = []
    for immunization_key in sorted(child_immunization_schedule):
        is_overdue = False
        vaccination_months = []
        immunization = child_immunization_schedule[immunization_key]
        schedId, schedule = immunization

        # horrible hack to skip months that are consecutive in the schedule
        skip = 0
        for monthnum in months:
            vm = VaccinationMonth(monthnum, None, False, '')

            for dose_key, doseMonth, consecutive_months in schedule:
                if monthnum == doseMonth:
                    vm.scheduleId = schedId
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


def vaccinate(request):
    return HttpResponse(json.dumps({"result": "success"}), content_type="application/x-javascript")
