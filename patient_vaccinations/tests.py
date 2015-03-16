"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from patient_vaccinations.views import Immunization, has_overlap
from django.test import TestCase


class An_immunization_schedule(TestCase):
    def test_finds_overlapping(self):
        """
        Finds all overlapping immunizaitons in the list
        """
        cis = {
            'Hepatitis B': (1,
                            [('first', 'Birth', 2, (0, 2)),
                             ('second', '1 month', 2, (1, 2)),
                             ('third', '6 months', 4, (6, 24)),
                             ('c', '11-12 years', 1, (132, 144))])}
        id, schedule = cis['Hepatitis B']
        ims = [Immunization(*i) for i in schedule]
        hs = has_overlap(ims[0], ims)
        print(hs)
        self.assertTrue(hs)
