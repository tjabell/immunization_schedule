from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from patient_vaccinations.models import get_vaccinations, Patient
import urllib
import requests
import json

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

    def contains(self, value):
        return self.start <= value and self.end >= value

    def overlaps(self, ordinal_range):
        return self.end >= ordinal_range.start

    def overlapped(self, ordinal_range):
        return self.start >= ordinal_range.end

    def __str__(self):
        return "{" + str(self.start) + "-" + str(self.end) + "}"


class Immunization(object):
    """Immunization information
    """
    def __init__(self, dose_key, age_can_be_taken,
                 consecutive_months, ordinal_range):
        super(Immunization, self).__init__()
        self.dose_key = dose_key
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


class Schedule(object):
        def __init__(self, name, id):
            self.name = name
            self.id = id
            self.vaccinations = []

        def addImmunization(self, immunizations):
            for view_month, month_ordinal in view_months:

                i = list(filter(
                    lambda x: x.age_can_be_taken == view_month or
                    x.ordinal_range.contains(month_ordinal),
                    immunizations))

                if(i == []):
                    vm = VaccinationMonth(False)
                else:
                    vm = VaccinationMonth(True)
                    vm.dose_key = i.dose_key
                    vm.dose = dose_map[i.dose_key]

                self.vaccinations.append(vm)



class VaccinationMonth(object):
    def __init__(self, dose_due):
        self.scheduleId = 0
        self.dose = ''
        self.dose_due = dose_due
        self.dose_key = ''
        self.consecutive_months = 0
        self.isPartOfRange = False
        self.overlaps = False
        self.overlapped = False


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

    schedules = []
    for immunization_key in sorted(child_immunization_schedule):
        immunization_schedule = child_immunization_schedule[immunization_key]
        scheduleId, schedule = immunization_schedule
        immunizations = [Immunization(*i) for i in schedule]
        schedule = Schedule(immunization_key, scheduleId)
        schedule.addImmunization(immunizations)
        context = {
            'patient': patient,
            'schedules': schedules,
            'view_months': view_months}

    return render(request, 'patient_schedule.html', context)


def vaccinate(request):
    return HttpResponse(json.dumps({"result": "success"}), content_type="application/x-javascript")
