from django.db import models
import datetime


class Patient(object):
    """Patient"""
    def __init__(self, id, name, birthdate):
        self.name = name
        self.id = id
        self.birthdate = birthdate
        self.vaccinations = []
        self.since = ''

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


class Vaccination(models.Model):
    """Vaccination for a patient"""
    def __init__(self):
        super(Vaccination, self).__init__()

    patient_id = models.IntegerField()
    immunization_id = models.IntegerField()
    date = models.DateField()
    dose = models.IntegerField()
