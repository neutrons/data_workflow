import pytest
from django.test import TestCase
from datetime import datetime
from django.utils import timezone

from reporting.report.models import Instrument
from reporting.dasmon.models import (
    Parameter,
    StatusVariable,
    StatusCache,
    ActiveInstrument,
    Signal,
    LegacyURL,
    UserNotification,
)


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


class SignalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        instrument = Instrument.objects.create(name="testInst")
        instrument.save()
        Signal.objects.create(
            instrument_id=instrument,
            name="testSignal",
            source="testSource",
            message="testMessage",
            level=1,
            timestamp=timezone.now(),
        )

    def test_name(self):
        s = Signal.objects.get(id=1)
        self.assertEqual(s.name, "testSignal")

    def test_name_max_length(self):
        s = Signal.objects.get(id=1)
        max_len = s._meta.get_field("name").max_length
        self.assertEqual(max_len, 128)

    def test_source(self):
        s = Signal.objects.get(id=1)
        self.assertEqual(s.source, "testSource")

    def test_source_max_length(self):
        s = Signal.objects.get(id=1)
        max_len = s._meta.get_field("source").max_length
        self.assertEqual(max_len, 40)

    def test_message(self):
        s = Signal.objects.get(id=1)
        self.assertEqual(s.message, "testMessage")

    def test_message_max_length(self):
        s = Signal.objects.get(id=1)
        max_len = s._meta.get_field("message").max_length
        self.assertEqual(max_len, 250)

    def test_level(self):
        s = Signal.objects.get(id=1)
        self.assertEqual(s.level, 1)

    def test_timestamp(self):
        s = Signal.objects.get(id=1)
        self.assertTrue(isinstance(s.timestamp, datetime))


class LegacyURLTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        instrument = Instrument.objects.create(name="testInst")
        instrument.save()
        LegacyURL.objects.create(
            instrument_id=instrument,
            url="testURL",
            long_name="testDescription",
        )

    def test_url(self):
        lu = LegacyURL.objects.get(id=1)
        self.assertEqual(lu.url, "testURL")

    def test_url_max_length(self):
        lu = LegacyURL.objects.get(id=1)
        max_len = lu._meta.get_field("url").max_length
        self.assertEqual(max_len, 128)

    def test_long_name(self):
        lu = LegacyURL.objects.get(id=1)
        self.assertEqual(lu.long_name, "testDescription")

    def test_long_name_max_length(self):
        lu = LegacyURL.objects.get(id=1)
        max_len = lu._meta.get_field("long_name").max_length
        self.assertEqual(max_len, 40)


class UserNotificationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE:
        # we cannot directly assign instruments due to its ManyToManyField
        # nature, therefore we settle for a zero checking for the instruments
        # field, i.e. not assigning any.
        UserNotification.objects.create(
            user_id=1,
            email="user@test.com",
            registered=True,
        )

    def test_user_id(self):
        un = UserNotification.objects.get(id=1)
        self.assertEqual(un.user_id, 1)

    def test_instruments(self):
        un = UserNotification.objects.get(id=1)
        self.assertEqual(un.instruments.all().count(), 0)

    def test_email(self):
        un = UserNotification.objects.get(id=1)
        self.assertEqual(un.email, "user@test.com")

    def test_registered(self):
        un = UserNotification.objects.get(id=1)
        self.assertTrue(un.registered)


if __name__ == "__main__":
    pytest.main([__file__])
