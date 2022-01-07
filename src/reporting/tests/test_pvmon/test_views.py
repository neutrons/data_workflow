import pytest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
import time
from report.models import Instrument
from pvmon.models import PVName
from pvmon.models import PV
from pvmon.models import PVCache
from pvmon.models import PVString
from pvmon.models import PVStringCache
from pvmon.models import MonitoredVariable


class PVMonitorViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(username="testuser", password="12345").save()
        inst = Instrument.objects.create(name="testinst")
        inst.save()
        pvname = PVName.objects.create(name="testpv")
        pvname.save()
        PV.objects.create(
            instrument=inst,
            name=pvname,
            value=1.0,
            status=0,
            update_time=int(time.time()),
        )
        PVCache.objects.create(
            instrument=inst,
            name=pvname,
            value=1.0,
            status=0,
            update_time=int(time.time()),
        )
        PVString.objects.create(
            instrument=inst,
            name=pvname,
            value="test",
            status=0,
            update_time=int(time.time()),
        )
        PVStringCache.objects.create(
            instrument=inst,
            name=pvname,
            value="test",
            status=0,
            update_time=int(time.time()),
        )
        MonitoredVariable.objects.create(
            instrument=inst,
            pv_name=pvname,
            rule_name="testRule",
        )

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="testinst").delete()
        PVName.objects.get(name="testpv").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/pvmon/testinst/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("pvmon:pv_monitor", args=["testinst"]))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("pvmon:pv_monitor", args=["testinst"]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pvmon/pv_monitor.html")

    def test_view_pv_list_in_context(self):
        response = self.client.get(reverse("pvmon:pv_monitor", args=["testinst"]))
        self.assertEqual(response.status_code, 200)
        # check the PV entry
        refstr = "'key': 'testpv', 'value': '1'"
        self.assertIn(refstr, str(response.context))
        # check the PVString entry
        refstr = "'key': 'testpv', 'value': 'test'"
        self.assertIn(refstr, str(response.context))
        print(response.context)


class GetUpdateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(username="testuser", password="12345").save()
        inst = Instrument.objects.create(name="testinst")
        inst.save()
        pvname = PVName.objects.create(name="testpv")
        pvname.save()
        PV.objects.create(
            instrument=inst,
            name=pvname,
            value=1.0,
            status=0,
            update_time=int(time.time()),
        )
        PVCache.objects.create(
            instrument=inst,
            name=pvname,
            value=1.0,
            status=0,
            update_time=int(time.time()),
        )
        PVString.objects.create(
            instrument=inst,
            name=pvname,
            value="test",
            status=0,
            update_time=int(time.time()),
        )
        PVStringCache.objects.create(
            instrument=inst,
            name=pvname,
            value="test",
            status=0,
            update_time=int(time.time()),
        )
        MonitoredVariable.objects.create(
            instrument=inst,
            pv_name=pvname,
            rule_name="testRule",
        )

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="testinst").delete()
        PVName.objects.get(name="testpv").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/pvmon/testinst/update/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("pvmon:get_update", args=["testinst"]))
        self.assertEqual(response.status_code, 200)

    def test_list_updated_content(self):
        inst = Instrument.objects.get(name="testinst")
        pvname = PVName.objects.get(name="testpv")
        pv = PV.objects.get(instrument=inst, name=pvname)
        pv.value = 2.0
        pv.save()
        pvcache = PVCache.objects.get(instrument=inst, name=pvname)
        pvcache.value = 2.0
        pvcache.save()
        pvstring = PVString.objects.get(instrument=inst, name=pvname)
        pvstring.value = "test2"
        pvstring.save()
        pvstringcache = PVStringCache.objects.get(instrument=inst, name=pvname)
        pvstringcache.value = "test2"
        pvstringcache.save()
        # get the update
        # NOTE: get_update is a backend update refresh, we still need to use
        #       the frontend to get the updated data
        response = self.client.get(reverse("pvmon:pv_monitor", args=["testinst"]))
        self.assertEqual(response.status_code, 200)
        # check the PV entry
        refstr = "'key': 'testpv', 'value': '2'"
        self.assertIn(refstr, str(response.context))
        # check the PVString entry
        refstr = "'key': 'testpv', 'value': 'test2'"


if __name__ == "__main__":
    pytest.main()
