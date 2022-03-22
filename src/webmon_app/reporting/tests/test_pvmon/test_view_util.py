import pytest
from unittest import mock
from django.test import TestCase
import time

from report.models import Instrument
from pvmon.models import PVName
from pvmon.models import PV
from pvmon.models import PVCache
from pvmon.models import PVString
from pvmon.models import PVStringCache


class ViewUtilTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        update_time = int(time.time())
        inst = Instrument.objects.create(name="testinst_pvmon")
        inst.save()
        for i_pv in range(4):
            pvn = PVName.objects.create(name=f"pv{i_pv}")
            pvn.save()
            for dt in range(10):
                PV.objects.create(
                    instrument=inst,
                    name=pvn,
                    value=i_pv * dt,
                    status=0,
                    update_time=update_time,
                ).save()
                PVCache.objects.create(
                    instrument=inst,
                    name=pvn,
                    value=i_pv * dt,
                    status=0,
                    update_time=update_time,
                ).save()
                PVString.objects.create(
                    instrument=inst,
                    name=pvn,
                    value=f"pv{i_pv}_dt{dt}",
                    status=0,
                    update_time=update_time,
                ).save()
                PVStringCache.objects.create(
                    instrument=inst,
                    name=pvn,
                    value=f"pv{i_pv}_dt{dt}",
                    status=0,
                    update_time=update_time,
                ).save()

    @classmethod
    def tearDownClass(cls):
        Instrument.objects.all().delete()
        PVName.objects.all().delete()

    def test_get_live_variables(self):
        from pvmon.view_util import get_live_variables

        # setup
        inst = Instrument.objects.get(name="testinst_pvmon")
        # -- null search
        data_dict = get_live_variables(None, inst, None)
        self.assertEqual(len(data_dict), 0)
        # -- use data from request
        request = mock.MagicMock()
        request.GET = {"vars": "pv0,pv1,pv2,pv3"}
        # call dict, but it is actually a nested list
        data_dict = get_live_variables(request, inst)
        self.assertEqual(len(data_dict), 4)
        data_pv3 = data_dict[3][1]
        self.assertEqual(data_pv3[-1][1], 27)
        # -- use args
        pvn3 = PVName.objects.get(name="pv3")
        data_dict = get_live_variables(None, inst, pvn3)
        self.assertEqual(len(data_dict), 1)
        data_pv3 = data_dict[0][1]
        self.assertEqual(data_pv3[-1][1], 27)

    def test_get_cached_variables(self):
        from pvmon.view_util import get_cached_variables

        # setup
        inst = Instrument.objects.get(name="testinst_pvmon")
        # check
        rst = get_cached_variables(inst)
        # NOTE:
        # 2 -> checking both PVCache and PVStringCache
        # 4 -> 4 unique pvs
        # 10 -> 10 data points each PV
        self.assertEqual(len(rst), 2 * 4 * 10)


if __name__ == "__main__":
    pytest.main()
