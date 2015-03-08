from django.db import models
import datetime


def get_vaccinations(patient_id):
    vacs = {}
    v = Vaccination()
    v.immunization_id = 1
    v.dose = 1
    v.patient_id = patient_id
    v.name = 'Hepatitis B'
    v.date = datetime.date(2015, 2, 5)

    vacs[(v.immunization_id, v.dose)] = v
    return vacs


class Patient(object):
    """Patient"""
    def __init__(self, id, name, birthdate):
        self.name = name
        self.id = id
        self.birthdate = birthdate
        self.vaccinations = []
    def is_overdue_for(self, immunization):
        # today = datetime.date.today()
        # months_old = (today - self.birthdate).days / 30
        is_overdue = True
        # TODO: needs to have a real implementation
        for vaccination in self.vaccinations:
            id, dose = vaccination
            imm_id, dose_sched = immunization
            if id == imm_id:
                is_overdue = False
        return is_overdue

# Create your models here.
class Vaccination(models.Model):
    """Vaccination for a patient"""
    def __init__(self):
        super(Vaccination, self).__init__()

    patient_id = models.IntegerField()
    immunization_id = models.IntegerField()
    date = models.DateField()
    dose = models.IntegerField()


# 'name' : (id, [(dose, sched_start_month, sched_end_month)]
