from datetime import datetime

import pytest
from django.test import TestCase

from reporting.pvmon.models import PV, Instrument, MonitoredVariable, PVCache, PVName, PVStringCache


class PVNameTest(TestCase):
    def test_str(self):
        pvname = PVName(name="test")
        self.assertEqual(str(pvname), "test")

    def test_max_length(self):
        pvname = PVName(name="test")
        max_len = pvname._meta.get_field("name").max_length
        self.assertEqual(max_len, 50)


class PVTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # the foreign key requirement makes it impossible to keep the test
        # self-contained.
        instrument = Instrument.objects.create(name="testInst")
        instrument.save()
        pvname = PVName.objects.create(name="testPV")
        pvname.save()
        PV.objects.create(
            instrument=instrument,
            name=pvname,
            value=1.0,
            status=0,
            timestamp=datetime.fromisoformat("2011-11-04T00:05:23Z"),
        )

    @classmethod
    def tearDownClass(cls):
        Instrument.objects.get(name="testInst").delete()
        PVName.objects.get(name="testPV").delete()

    def test_value(self):
        pv = PV.objects.get(id=1)
        self.assertEqual(pv.value, 1.0)

    def test_status(self):
        pv = PV.objects.get(id=1)
        self.assertEqual(pv.status, 0)

    def test_timestamp(self):
        pv = PV.objects.get(id=1)
        self.assertEqual(pv.timestamp, datetime.fromisoformat("2011-11-04T00:05:23Z"))


class PVCacheTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        instrument = Instrument.objects.create(name="testInst")
        instrument.save()
        pvname = PVName.objects.create(name="testPV")
        pvname.save()
        PVCache.objects.create(
            instrument=instrument,
            name=pvname,
            value=1.0,
            status=0,
            timestamp=datetime.fromisoformat("2011-11-04T00:05:23Z"),
        )

    @classmethod
    def tearDownClass(cls):
        Instrument.objects.get(name="testInst").delete()
        PVName.objects.get(name="testPV").delete()

    def test_value(self):
        pv = PVCache.objects.get(id=1)
        self.assertEqual(pv.value, 1.0)

    def test_status(self):
        pv = PVCache.objects.get(id=1)
        self.assertEqual(pv.status, 0)

    def test_timestamp(self):
        pv = PVCache.objects.get(id=1)
        self.assertEqual(pv.timestamp, datetime.fromisoformat("2011-11-04T00:05:23Z"))


class PVStringCacheTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        instrument = Instrument.objects.create(name="testInst")
        instrument.save()
        pvname = PVName.objects.create(name="testPV")
        pvname.save()
        PVStringCache.objects.create(
            instrument=instrument,
            name=pvname,
            value="test",
            status=0,
            timestamp=datetime.fromisoformat("2011-11-04T00:05:23Z"),
        )

    @classmethod
    def tearDownClass(cls):
        Instrument.objects.get(name="testInst").delete()
        PVName.objects.get(name="testPV").delete()

    def test_value(self):
        pv = PVStringCache.objects.get(id=1)
        self.assertEqual(pv.value, "test")

    def test_status(self):
        pv = PVStringCache.objects.get(id=1)
        self.assertEqual(pv.status, 0)

    def test_timestamp(self):
        pv = PVStringCache.objects.get(id=1)
        self.assertEqual(pv.timestamp, datetime.fromisoformat("2011-11-04T00:05:23Z"))


class MonitoredVariableTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        instrument = Instrument.objects.create(name="testInst")
        instrument.save()
        pvname = PVName.objects.create(name="testPV")
        pvname.save()
        MonitoredVariable.objects.create(
            instrument=instrument,
            pv_name=pvname,
            rule_name="testRule",
        )

    @classmethod
    def tearDownClass(cls):
        Instrument.objects.get(name="testInst").delete()
        PVName.objects.get(name="testPV").delete()

    def test_rule_name(self):
        pv = MonitoredVariable.objects.get(id=1)
        self.assertEqual(pv.rule_name, "testRule")

    def test_rule_name_max_length(self):
        pv = MonitoredVariable.objects.get(id=1)
        max_len = pv._meta.get_field("rule_name").max_length
        self.assertEqual(max_len, 50)

    def test_created_field_exists(self):
        pv = MonitoredVariable.objects.get(id=1)
        self.assertTrue(hasattr(pv, "created"))
        self.assertIsNotNone(pv.created)

    def test_updated_field_exists(self):
        pv = MonitoredVariable.objects.get(id=1)
        self.assertTrue(hasattr(pv, "updated"))
        self.assertIsNotNone(pv.updated)

    def test_created_auto_now_add(self):
        # Test that created field has auto_now_add=True
        pv = MonitoredVariable.objects.get(id=1)
        created_field = pv._meta.get_field("created")
        self.assertTrue(created_field.auto_now_add)

    def test_updated_auto_now(self):
        # Test that updated field has auto_now=True
        pv = MonitoredVariable.objects.get(id=1)
        updated_field = pv._meta.get_field("updated")
        self.assertTrue(updated_field.auto_now)


if __name__ == "__main__":
    pytest.main()
