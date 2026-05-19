from datetime import datetime

import pytest
from django.test import TestCase
from django.utils import timezone

from reporting.dasmon.models import (
    ActiveInstrument,
    Parameter,
    StatusCache,
    StatusVariable,
)
from reporting.report.models import Instrument


class ParameterTest(TestCase):
    def test_str(self):
        p = Parameter(name="test")
        assert str(p) == "test"


class StatusVariableTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # the foreign key requirement makes it impossible to keep the test
        # self-contained.
        instrument = Instrument.objects.create(name="testInst")
        instrument.save()
        parameter = Parameter.objects.create(name="testParam")
        parameter.save()
        StatusVariable.objects.create(
            instrument_id=instrument,
            key_id=parameter,
            value="testvalue",
        )

    def test_value(self):
        sv = StatusVariable.objects.get(id=1)
        self.assertEqual(sv.value, "testvalue")

    def test_value_maxlength(self):
        sv = StatusVariable.objects.get(id=1)
        max_len = sv._meta.get_field("value").max_length
        self.assertEqual(max_len, 128)

    def test_timestamp(self):
        sv = StatusVariable.objects.get(id=1)
        self.assertTrue(isinstance(sv.timestamp, datetime))


class StatusCacheTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # the foreign key requirement makes it impossible to keep the test
        # self-contained.
        instrument = Instrument.objects.create(name="testInst")
        instrument.save()
        parameter = Parameter.objects.create(name="testParam")
        parameter.save()
        StatusCache.objects.create(
            instrument_id=instrument,
            key_id=parameter,
            value="testvalue",
            timestamp=timezone.now(),
        )

    def test_value(self):
        sc = StatusCache.objects.get(id=1)
        self.assertEqual(sc.value, "testvalue")

    def test_value_maxlength(self):
        sc = StatusCache.objects.get(id=1)
        max_len = sc._meta.get_field("value").max_length
        self.assertEqual(max_len, 128)

    def test_timestamp(self):
        sc = StatusCache.objects.get(id=1)
        self.assertTrue(isinstance(sc.timestamp, datetime))


# NOTE:
# ActiveInstrumentManager is tested within ActiveInstrumentTest as it is
# the query manager that facilitates the get method.
class ActiveInstrumentTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        instrument = Instrument.objects.create(name="testInst")
        instrument.save()
        ActiveInstrument.objects.create(
            instrument_id=instrument,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )

    def test_is_alive(self):
        ai = ActiveInstrument.objects.get(id=1)
        self.assertTrue(ai.is_alive)

    def test_is_adara(self):
        ai = ActiveInstrument.objects.get(id=1)
        self.assertTrue(ai.is_adara)

    def test_has_pvsd(self):
        ai = ActiveInstrument.objects.get(id=1)
        self.assertTrue(ai.has_pvsd)

    def test_has_pvstreamer(self):
        ai = ActiveInstrument.objects.get(id=1)
        self.assertTrue(ai.has_pvstreamer)


if __name__ == "__main__":
    pytest.main([__file__])
