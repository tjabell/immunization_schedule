"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
from patient_vaccinations.views import Immunization, has_overlap,Schedule, child_immunization_schedule, OrdinalRange
from django.test import TestCase


class An_immunization_schedule1(TestCase):
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
        self.assertTrue(hs)

    def test_makes_correct_schedule(self):
        """
        Generates the correct schedule for the vaccinations
        """

        for k in child_immunization_schedule:
            sid, schedule = child_immunization_schedule[k]
            immunizations = [Immunization(*ia) for ia in schedule]
            S = Schedule(k, sid)
            S.addImmunizations(immunizations)
            print(S.vaccinations)

    def test_ordinal_range_early_overlaps_later(self):
        first = OrdinalRange(0, 1)
        second = OrdinalRange(1, 2)
        self.assertTrue(first.overlaps(second))

    def test_ordinal_range_later_overlapped_by_earlier(self):
        first = OrdinalRange(0, 1)
        second = OrdinalRange(1, 2)
        self.assertTrue(second.overlapped(first))

    def test_ordinal_range_later_doesnt_overlap_earlier(self):
        first = OrdinalRange(0, 1)
        second = OrdinalRange(1, 2)
        self.assertFalse(second.overlaps(first))

    def test_ordinal_range_earlier_not_overlapped_by_later(self):
        first = OrdinalRange(0, 1)
        second = OrdinalRange(1, 2)
        self.assertFalse(second.overlaps(first))
