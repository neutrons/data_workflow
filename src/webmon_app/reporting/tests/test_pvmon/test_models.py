import pytest
from django.test import TestCase

from reporting.pvmon.models import PVName, PV, PVCache, PVString, PVStringCache, MonitoredVariable, Instrument


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
            update_time=1,
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

    def test_update_time(self):
        pv = PV.objects.get(id=1)
        self.assertEqual(pv.update_time, 1)


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
            update_time=1,
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

    def test_update_time(self):
        pv = PVCache.objects.get(id=1)
        self.assertEqual(pv.update_time, 1)


class PVStringTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        instrument = Instrument.objects.create(name="testInst")
        instrument.save()
        pvname = PVName.objects.create(name="testPV")
        pvname.save()
        PVString.objects.create(
            instrument=instrument,
            name=pvname,
            value="test",
            status=0,
            update_time=1,
        )

    @classmethod
    def tearDownClass(cls):
        Instrument.objects.get(name="testInst").delete()
        PVName.objects.get(name="testPV").delete()

    def test_value(self):
        pv = PVString.objects.get(id=1)
        self.assertEqual(pv.value, "test")

    def test_status(self):
        pv = PVString.objects.get(id=1)
        self.assertEqual(pv.status, 0)

    def test_update_time(self):
        pv = PVString.objects.get(id=1)
        self.assertEqual(pv.update_time, 1)


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
            update_time=1,
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

    def test_update_time(self):
        pv = PVStringCache.objects.get(id=1)
        self.assertEqual(pv.update_time, 1)


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


if __name__ == "__main__":
    pytest.main()
