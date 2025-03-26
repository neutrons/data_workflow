import pytest
from unittest import mock
from django.test import TestCase
import datetime

import django
from reporting import dasmon, users
from django.conf import settings
from django.contrib.auth.models import Group
from django.utils import timezone

from reporting.report.models import Instrument, Information, RunStatus, StatusQueue, Error, WorkflowSummary
from reporting.dasmon.models import ActiveInstrument, Parameter, StatusCache, StatusVariable, Signal
from workflow.database.report.models import DataRun
from workflow.database.report.models import IPTS


# make flake8 happy
_ = [django, dasmon, users]


class ViewUtilTest(TestCase):
    @classmethod
    def setUpClass(cls):
        inst = Instrument.objects.create(name="testinst")
        inst.save()
        ActiveInstrument.objects.create(
            instrument_id=inst,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
        para = Parameter.objects.create(name="testParam")
        para.save()
        run_number = Parameter.objects.create(name="run_number")
        run_number.save()
        cnt_rate = Parameter.objects.create(name="cnt_rate")
        cnt_rate.save()
        proposal_id = Parameter.objects.create(name="proposal_id")
        proposal_id.save()
        run_title = Parameter.objects.create(name="run_title")
        run_title.save()

        # we add the run_title twice to check that the newest one is returned
        for p, v in zip(
            [para, run_number, cnt_rate, proposal_id, run_title, run_title],
            ["testValue", 0, 1, 2, "testRunTitle", "testRunTitleNew"],
        ):
            StatusVariable.objects.create(
                instrument_id=inst,
                key_id=p,
                value=v,
            )
            StatusCache.objects.create(
                instrument_id=inst,
                key_id=p,
                value=v,
                timestamp=timezone.now(),
            )

        # add common services
        common = Instrument.objects.create(name="common")
        common.save()
        name_workflowmgr = settings.SYSTEM_STATUS_PREFIX + "workflowmgr"
        para_workflowmgr = Parameter.objects.create(name=name_workflowmgr)
        para_workflowmgr.save()
        StatusVariable.objects.create(
            instrument_id=common,
            key_id=para_workflowmgr,
            value=0,
        )
        StatusCache.objects.create(
            instrument_id=common,
            key_id=para_workflowmgr,
            value=0,
            timestamp=timezone.now(),
        )

        ipts = IPTS.objects.create(expt_name="testexp")
        ipts.save()
        sq_DataReady = StatusQueue(name="POSTPROCESS.DATA_READY", is_workflow_input=True)
        sq_DataReady.save()
        for run_number in range(10):
            run = DataRun.objects.create(
                run_number=run_number,
                ipts_id=ipts,
                instrument_id=inst,
                file=f"tmp/test_{run_number}.nxs",
            )
            run.save()
            WorkflowSummary.objects.create(
                run_id=run,
                complete=run_number % 2 == 0,
                catalog_started=True,
                cataloged=True,
                reduction_needed=False,
                reduction_started=True,
                reduced=True,
                reduction_cataloged=True,
                reduction_catalog_started=True,
            )
            if run_number > 4 or run_number % 2 == 0:
                rs2 = RunStatus.objects.create(
                    run_id=run,
                    queue_id=sq_DataReady,
                    message_id=f"msg: test_run_{run_number}",
                )
                rs2.save()

                if run_number == 7:
                    e = Error(run_status_id=rs2, description="test_error")
                    e.save()

    @classmethod
    def tearDownClass(cls):
        Instrument.objects.all().delete()
        Parameter.objects.all().delete()
        StatusQueue.objects.all().delete()
        DataRun.objects.all().delete()
        WorkflowSummary.objects.all().delete()

    def test_get_monitor_breadcrumbs(self):
        inst = Instrument.objects.get(name="testinst")

        # test the function
        from reporting.dasmon.view_util import get_monitor_breadcrumbs

        breadcrumbs = get_monitor_breadcrumbs(inst, "TestView")
        assert breadcrumbs[-8:] == "TestView"

    def test_get_cached_variables(self):
        inst = Instrument.objects.get(name="testinst")

        # ref val
        ref_val = {
            "key": "testParam",
            "value": "testValue",
        }

        # test the function
        from reporting.dasmon.view_util import get_cached_variables

        pairs = get_cached_variables(inst, monitored_only=False)
        pairs_monitoredOnly = get_cached_variables(inst, monitored_only=True)
        for d in pairs:
            if d["key"] == "testParam":
                assert d["value"] == ref_val["value"]
            if d["key"] == "run_title":
                # expect run_title==testRunTitleNew because it's newest
                assert d["value"] == "testRunTitleNew"
        for d in pairs_monitoredOnly:
            if d["key"] == "testParam":
                assert d["value"] == ref_val["value"]

    def test_get_latest(self):
        inst = Instrument.objects.get(name="testinst")
        para = Parameter.objects.get(name="testParam")

        # test the function
        from reporting.dasmon.view_util import get_latest

        # -- record in StatusCache
        latest = get_latest(inst, para)
        assert latest.value == "testValue"
        # -- record no in StatusCache but in StatusVariable
        inst2 = Instrument.objects.create(name="testInst2")
        inst2.save()
        para2 = Parameter.objects.create(name="testParam2")
        para2.save()
        StatusVariable.objects.create(
            instrument_id=inst2,
            key_id=para2,
            value="testValue2",
        )
        latest2 = get_latest(inst2, para2)
        assert latest2.value == "testValue2"

    def test_is_running(self):
        from reporting.dasmon.view_util import is_running

        # -- Unknown
        # NOTE: the status of this instrument should be unknown as we never
        #       add it to the table
        inst = Instrument.objects.create(name="testInst_unknown")
        inst.save()
        assert is_running(inst) == "Unknown"
        # -- Recording
        inst_recording = Instrument.objects.create(name="testInst_recording")
        inst_recording.save()
        para_recording = Parameter.objects.create(name="recording")
        para_recording.save()
        ActiveInstrument.objects.create(
            instrument_id=inst_recording,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
        StatusVariable.objects.create(
            instrument_id=inst_recording,
            key_id=para_recording,
            value="true",
        )
        StatusCache.objects.create(
            instrument_id=inst_recording,
            key_id=para_recording,
            value="true",
            timestamp=timezone.now(),
        )
        assert is_running(inst_recording) == "Recording"
        # -- Paused
        inst_paused = Instrument.objects.create(name="testInst_paused")
        inst_paused.save()
        para_paused = Parameter.objects.create(name="paused")
        para_paused.save()
        ActiveInstrument.objects.create(
            instrument_id=inst_paused,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
        StatusVariable.objects.create(
            instrument_id=inst_paused,
            key_id=para_recording,
            value="true",
        )
        StatusVariable.objects.create(
            instrument_id=inst_paused,
            key_id=para_paused,
            value="true",
        )
        StatusCache.objects.create(
            instrument_id=inst_paused,
            key_id=para_recording,
            value="true",
            timestamp=timezone.now(),
        )
        StatusCache.objects.create(
            instrument_id=inst_paused,
            key_id=para_paused,
            value="true",
            timestamp=timezone.now(),
        )
        assert is_running(inst_paused) == "Paused"
        # -- Stopped
        inst_stopped = Instrument.objects.create(name="testInst_stopped")
        inst_stopped.save()
        ActiveInstrument.objects.create(
            instrument_id=inst_stopped,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
        StatusVariable.objects.create(
            instrument_id=inst_stopped,
            key_id=para_recording,
            value="false",
        )
        StatusVariable.objects.create(
            instrument_id=inst_stopped,
            key_id=para_paused,
            value="false",
        )
        StatusCache.objects.create(
            instrument_id=inst_stopped,
            key_id=para_recording,
            value="false",
            timestamp=timezone.now(),
        )
        StatusCache.objects.create(
            instrument_id=inst_stopped,
            key_id=para_paused,
            value="false",
            timestamp=timezone.now(),
        )
        assert is_running(inst_stopped) == "Stopped"

    @mock.patch(("reporting.dasmon.view_util.get_pvstreamer_status"), return_value="test")
    @mock.patch(("reporting.dasmon.view_util.get_component_status"), return_value="test")
    @mock.patch(("reporting.dasmon.view_util.get_workflow_status"), return_value="test")
    def test_get_system_health(self, mock_workflow, mock_component, mock_pvstreamer):
        # make flake8 happy
        _ = [mock_pvstreamer, mock_component, mock_workflow]
        # NOTE:
        # the mocked functions have their own unit tests
        inst = Instrument.objects.get(name="testinst")
        from reporting.dasmon.view_util import get_system_health

        health = get_system_health(inst)
        for k, v in health.items():
            if k in ("catalog", "reduction"):
                assert v == 0
            else:
                assert v == "test"

    def test_get_workflow_status(self):
        from reporting.dasmon.view_util import get_workflow_status

        # -- trigger red
        status = get_workflow_status(red_timeout=0)
        assert status == 2
        # -- trigger yellow
        status = get_workflow_status(red_timeout=65535, yellow_timeout=0)
        assert status == 1
        # -- trigger default
        status = get_workflow_status(red_timeout=65535, yellow_timeout=65535)
        assert status == 0

    def test_get_component_status(self):
        from reporting.dasmon.view_util import get_component_status

        # -- non adara case
        inst_nonadara = Instrument.objects.create(name="testInst_nonadara")
        inst_nonadara.save()
        ActiveInstrument.objects.create(
            instrument_id=inst_nonadara,
            is_alive=True,
            is_adara=False,
            has_pvsd=True,
            has_pvstreamer=True,
        )
        cmpt_status = get_component_status(inst_nonadara)
        assert cmpt_status == -1
        # -- adara inst nonresponsive, status: 2
        inst_adara_nonresponsive = Instrument.objects.create(name="testInst_adara_nonresponsive")
        inst_adara_nonresponsive.save()
        name_process = settings.SYSTEM_STATUS_PREFIX + "test"
        para_adara_nonresponsive = Parameter.objects.create(name=name_process)
        para_adara_nonresponsive.save()
        ActiveInstrument.objects.create(
            instrument_id=inst_adara_nonresponsive,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
        StatusVariable.objects.create(
            instrument_id=inst_adara_nonresponsive,
            key_id=para_adara_nonresponsive,
            value=2,
        )
        StatusCache.objects.create(
            instrument_id=inst_adara_nonresponsive,
            key_id=para_adara_nonresponsive,
            value=2,
            timestamp=timezone.now(),
        )
        cmpt_status = get_component_status(inst_adara_nonresponsive, process="test")
        assert cmpt_status == 2
        # -- adara inst responsive
        #    red: 2
        #    yellow: 1
        #    good: 0
        inst = Instrument.objects.create(name="testInst_adara_responsive")
        inst.save()
        name_process = settings.SYSTEM_STATUS_PREFIX + "ok"
        para_adara_responsive = Parameter.objects.create(name=name_process)
        para_adara_responsive.save()
        ActiveInstrument.objects.create(
            instrument_id=inst,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
        StatusVariable.objects.create(
            instrument_id=inst,
            key_id=para_adara_responsive,
            value=0,
        )
        StatusCache.objects.create(
            instrument_id=inst,
            key_id=para_adara_responsive,
            value=0,
            timestamp=timezone.now(),
        )
        cmpt_status = get_component_status(inst, red_timeout=0, process="ok")
        assert cmpt_status == 2
        cmpt_status = get_component_status(inst, red_timeout=65535, yellow_timeout=0, process="ok")
        assert cmpt_status == 1
        cmpt_status = get_component_status(inst, red_timeout=65535, yellow_timeout=65535, process="ok")
        assert cmpt_status == 0

    @mock.patch(("reporting.dasmon.view_util.get_component_status"), return_value=0)
    def test_get_pvstreamer_status(self, mock_get_component_status):
        from reporting.dasmon.view_util import get_pvstreamer_status

        # make flake8 happy
        _ = mock_get_component_status
        # -- no pvsd and pvstreamer: -1
        inst_nopvsdstreamer = Instrument.objects.create(name="testInst_nopvsdstreamer")
        inst_nopvsdstreamer.save()
        ActiveInstrument.objects.create(
            instrument_id=inst_nopvsdstreamer,
            is_alive=True,
            is_adara=True,
            has_pvsd=False,
            has_pvstreamer=False,
        )
        pvstreamer_status = get_pvstreamer_status(inst_nopvsdstreamer)
        assert pvstreamer_status == -1
        # -- has pvsd or pvstreamer: 0
        inst_pvsdstreamer = Instrument.objects.create(name="testInst_pvsdstreamer")
        inst_pvsdstreamer.save()
        ActiveInstrument.objects.create(
            instrument_id=inst_pvsdstreamer,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
        pvstreamer_status = get_pvstreamer_status(inst_pvsdstreamer)
        assert pvstreamer_status == 0

    @mock.patch(("reporting.dasmon.view_util.is_running"), return_value=0)
    @mock.patch(("reporting.dasmon.view_util.get_system_health"), return_value=0)
    @mock.patch(("django.urls.reverse"), return_value="test")
    @mock.patch(("reporting.users.view_util.is_instrument_staff"), return_value=True)
    def test_fill_template_values(
        self,
        mock_is_instrument_staff,
        mock_reverse,
        mock_get_system_health,
        mock_is_running,
    ):
        # make flake8 happy
        _ = [
            mock_is_instrument_staff,
            mock_reverse,
            mock_get_system_health,
            mock_is_running,
        ]
        # test
        from reporting.dasmon.view_util import fill_template_values

        template = fill_template_values(1, instrument="testinst")
        # check
        assert template["instrument"] == "testinst"
        assert template["is_instrument_staff"]
        assert template["is_adara"]
        assert template["profile_url"] == "/dasmon/notifications/"
        assert template["live_monitor_url"] == "/dasmon/testinst/"
        assert template["live_runs_url"] == "/dasmon/testinst/runs/"
        assert template["live_pv_url"] == "/pvmon/testinst/"
        assert template["dasmon_url"] is None
        assert template["das_status"] == 0
        assert template["recording_status"] == 0
        assert template["run_number"] == "0"
        assert template["count_rate"] == "-"
        assert template["proposal_id"] == "2"
        assert template["run_title"] == "testRunTitleNew"

    def test_get_live_variables(self):
        from reporting.dasmon.view_util import get_live_variables

        # mock the HTTP request object
        request = mock.Mock()
        request.GET = {
            "var": "run_number",
            "instrument": "testinst",
        }
        inst = Instrument.objects.get(name="testinst")
        # test
        # NOTE:
        # since we don't really have any live run data during testing, the best
        # we can do here is to check if the func runs without errors
        get_live_variables(request, inst)

    def test_workflow_diagnostics(self):
        from reporting.dasmon.view_util import workflow_diagnostics

        wf_diag = workflow_diagnostics()
        # NOTE: since we are missing a lot of entries during testing, we can
        #       only check the ones that do exist at this point.
        assert wf_diag["status"] == 0
        assert wf_diag["dasmon_listener_warning"] is False
        # print(wf_diag)
        # {'status': 0,
        #  'status_time': datetime.datetime(2022, 1, 5, 13, 8, 2),
        #  'conditions': [],
        #  'dasmon_listener_warning': False,
        #  'processes': [],
        #  'dasmon_listener': []}

    def test_postprocessing_diagnostics(self):
        from reporting.dasmon.view_util import postprocessing_diagnostics

        # add postprocessing services
        common = Instrument.objects.get(name="common")
        name_postprocessor = settings.SYSTEM_STATUS_PREFIX + "autoreducer4.com"
        para_postprocessor = Parameter.objects.create(name=name_postprocessor)
        para_postprocessor.save()
        StatusCache.objects.create(
            instrument_id=common,
            key_id=para_postprocessor,
            value=0,
            timestamp=timezone.now(),
        )
        para_postprocessor_pid = Parameter.objects.create(name=name_postprocessor + "_pid")
        para_postprocessor_pid.save()
        StatusCache.objects.create(
            instrument_id=common,
            key_id=para_postprocessor_pid,
            value=7,
            timestamp=timezone.now(),
        )

        # create StatusQueue, DataRun, RunStatus and Information needed for test
        inst = Instrument.objects.get(name="testinst")
        queue = StatusQueue(name="REDUCTION.COMPLETE")
        queue.save()
        ipts = IPTS(expt_name="IPTS-42")
        ipts.save()
        dataRun = DataRun(run_number=42, ipts_id=ipts, instrument_id=inst, file="/filename")
        dataRun.save()
        runStatus = RunStatus(run_id=dataRun, queue_id=queue)
        runStatus.save()
        info = Information(run_status_id=runStatus, description="autoreducer4.com")
        info.save()

        red_diag = postprocessing_diagnostics()
        # NOTE: we don't have any postprocessing data during testing, so only
        #       test the entry that does exist
        assert red_diag["catalog_status"] == 0
        assert red_diag["reduction_status"] == 0
        assert len(red_diag["conditions"]) == 0

        # for nodes we have data to check
        assert len(red_diag["ar_nodes"]) == 3
        for i in range(3):
            assert "time" in red_diag["ar_nodes"][i]
            assert red_diag["ar_nodes"][i]["node"] == "autoreducer4.com"

        msgs = [node["msg"] for node in red_diag["ar_nodes"] if "msg" in node]
        print(msgs)
        assert len(msgs) == 2
        assert "PID: 7" in msgs
        assert "Last msg: testinst_42: REDUCTION.COMPLETE" in msgs

    def test_pvstreamer_diagnostics(self):
        from reporting.dasmon.view_util import pvstreamer_diagnostics

        inst = Instrument.objects.create(name="testinst_pvstreamer")
        inst.save()
        name_para = settings.SYSTEM_STATUS_PREFIX + "pvstreamer_test"
        para = Parameter.objects.create(name=name_para)
        para.save()
        ActiveInstrument.objects.create(
            instrument_id=inst,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
        StatusVariable.objects.create(
            instrument_id=inst,
            key_id=para,
            value=0,
        )
        StatusCache.objects.create(
            instrument_id=inst,
            key_id=para,
            value=0,
            timestamp=timezone.now(),
        )
        # test
        pvstreamer_diag = pvstreamer_diagnostics(inst, process="pvstreamer_test")
        # print(pvstreamer_diag)
        # {'status': 0,
        #  'status_time': datetime.datetime(2022, 1, 5, 13, 9, 38),
        #  'conditions': [],
        #  'dasmon_listener_warning': False}
        assert pvstreamer_diag["status"] == 0
        assert pvstreamer_diag["dasmon_listener_warning"] is False

    def test_dasmon_diagnostics(self):
        from reporting.dasmon.view_util import dasmon_diagnostics

        # make test inst
        inst = Instrument.objects.create(name="testinst_dasmon")
        inst.save()
        name_para = settings.SYSTEM_STATUS_PREFIX + "dasmon"
        para = Parameter.objects.create(name=name_para)
        para.save()
        ActiveInstrument.objects.create(
            instrument_id=inst,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
        StatusVariable.objects.create(
            instrument_id=inst,
            key_id=para,
            value=0,
        )
        StatusCache.objects.create(
            instrument_id=inst,
            key_id=para,
            value=0,
            timestamp=timezone.now(),
        )
        # test
        dasmon_diag = dasmon_diagnostics(inst)
        # print(dasmon_diag)
        # {'status': 0,
        #  'status_time': datetime.datetime(2022, 1, 5, 13, 14, 2),
        #  'pv_time': datetime.datetime(2000, 1, 1, 0, 1, tzinfo=<DstTzInfo 'America/Chicago' LMT-1 day, 18:09:00 STD>),
        #  'amq_time': datetime.datetime(2022, 1, 5, 13, 14, 2),
        #  'conditions': ['No PV updates in the past 1641406442.6972866 seconds',
        #                 'DASMON is up but not writing to the DB: check pvsd'],
        #  'dasmon_listener_warning': False}
        assert dasmon_diag["status"] == 0
        assert dasmon_diag["dasmon_listener_warning"] is False

    def test_get_run_list_ipts(self):
        from reporting.dasmon.view_util import get_run_list_ipts

        instrument_id = Instrument.objects.get(name="testinst")
        ipts_id = IPTS.objects.get(expt_name="testexp")

        # reversed should have run number 9 first
        rst, count, filtered_count = get_run_list_ipts(instrument_id, ipts_id, 0, 10, "created_on", True, "", "", "")
        assert count == 10
        assert filtered_count == 10
        assert rst[0].run_number == 9

        # not reversed should have run number 0 first
        rst, count, filtered_count = get_run_list_ipts(instrument_id, ipts_id, 0, 10, "created_on", False, "", "", "")
        assert count == 10
        assert filtered_count == 10
        assert rst[0].run_number == 0

        # reversed should have run number 9 first
        rst, count, filtered_count = get_run_list_ipts(instrument_id, ipts_id, 0, 10, "run_number", True, "", "", "")
        assert count == 10
        assert filtered_count == 10
        assert rst[0].run_number == 9

        # not reversed should have run number 0 first
        rst, count, filtered_count = get_run_list_ipts(instrument_id, ipts_id, 0, 10, "run_number", False, "", "", "")
        assert count == 10
        assert filtered_count == 10
        assert rst[0].run_number == 0

        # check searching and limits

        # limit = 2
        rst, count, filtered_count = get_run_list_ipts(instrument_id, ipts_id, 0, 2, "created_on", True, "", "", "")
        assert filtered_count == 10
        assert count == 10
        assert rst[0].run_number == 9
        assert len(rst) == 2

        # run number
        rst, count, filtered_count = get_run_list_ipts(instrument_id, ipts_id, 0, 10, "created_on", True, "2", "", "")
        assert filtered_count == 1
        assert count == 10
        assert rst[0].run_number == 2

        # date, old date should return nothing
        rst, count, filtered_count = get_run_list_ipts(
            instrument_id, ipts_id, 0, 10, "created_on", True, "", "1900-01-01", ""
        )
        assert filtered_count == 0
        assert count == 10
        assert len(rst) == 0

        # date, todays date should return all
        rst, count, filtered_count = get_run_list_ipts(
            instrument_id, ipts_id, 0, 10, "created_on", True, "", str(datetime.date.today()), ""
        )
        assert filtered_count == 10
        assert count == 10
        assert rst[0].run_number == 9

        # complete status
        rst, count, filtered_count = get_run_list_ipts(
            instrument_id, ipts_id, 0, 10, "created_on", True, "", "", "complete"
        )
        assert filtered_count == 5
        assert count == 10
        assert rst[0].run_number == 8

        # error status
        rst, count, filtered_count = get_run_list_ipts(
            instrument_id, ipts_id, 0, 10, "created_on", True, "", "", "error"
        )
        assert filtered_count == 1
        assert count == 10
        assert rst[0].run_number == 7

        # incomplete status
        rst, count, filtered_count = get_run_list_ipts(
            instrument_id, ipts_id, 0, 10, "created_on", True, "", "", "incomplete"
        )
        assert filtered_count == 2
        assert count == 10
        assert rst[0].run_number == 9

        # acquiring status
        rst, count, filtered_count = get_run_list_ipts(
            instrument_id, ipts_id, 0, 10, "created_on", True, "", "", "acquiring"
        )
        assert filtered_count == 2
        assert count == 10
        assert rst[0].run_number == 3

    def test_get_run_list_instrument_newest(self):
        from reporting.dasmon.view_util import get_run_list_instrument_newest

        instrument_id = Instrument.objects.get(name="testinst")

        rst, count, filtered_count = get_run_list_instrument_newest(instrument_id, 0, 10, "", "", "")
        assert count == 10
        assert filtered_count == 10
        assert rst[0].run_number == 9

        # check searching and limits

        # limit = 2
        rst, count, filtered_count = get_run_list_instrument_newest(instrument_id, 0, 2, "", "", "")
        assert count == 10
        assert filtered_count == 10
        assert rst[0].run_number == 9
        assert len(rst) == 2

        # run number
        rst, count, filtered_count = get_run_list_instrument_newest(instrument_id, 0, 10, "2", "", "")
        assert count == 10
        assert filtered_count == 1
        assert rst[0].run_number == 2

        # date, old date should return nothing
        rst, count, filtered_count = get_run_list_instrument_newest(instrument_id, 0, 10, "", "1900-01-01", "")
        assert count == 10
        assert filtered_count == 0
        assert len(rst) == 0

        # date, todays date should return all
        rst, count, filtered_count = get_run_list_instrument_newest(
            instrument_id, 0, 10, "", str(datetime.date.today()), ""
        )
        assert count == 10
        assert filtered_count == 10
        assert rst[0].run_number == 9

        # complete status
        rst, count, filtered_count = get_run_list_instrument_newest(instrument_id, 0, 10, "", "", "complete")
        assert count == 10
        assert filtered_count == 5
        assert rst[0].run_number == 8

        # error status
        rst, count, filtered_count = get_run_list_instrument_newest(instrument_id, 0, 10, "", "", "error")
        assert count == 10
        assert filtered_count == 1
        assert rst[0].run_number == 7

        # incomplete status
        rst, count, filtered_count = get_run_list_instrument_newest(instrument_id, 0, 10, "", "", "incomplete")
        assert count == 10
        assert filtered_count == 2
        assert rst[0].run_number == 9

        # acquiring status
        rst, count, filtered_count = get_run_list_instrument_newest(instrument_id, 0, 10, "", "", "acquiring")
        assert count == 10
        assert filtered_count == 2
        assert rst[0].run_number == 3

    def test_get_run_list_newest(self):
        from reporting.dasmon.view_util import get_run_list_newest

        rst, count, filtered_count = get_run_list_newest(0, 10, "", "", "", "")
        assert count == 10
        assert filtered_count == 10
        assert rst[0].run_number == 9
        # check searching and limits

        # limit = 2
        rst, count, filtered_count = get_run_list_newest(0, 2, "", "", "", "")
        assert count == 10
        assert filtered_count == 10
        assert rst[0].run_number == 9
        assert len(rst) == 2

        # correct instrument
        rst, count, filtered_count = get_run_list_newest(0, 10, "testinst", "", "", "")
        assert count == 10
        assert filtered_count == 10
        assert rst[0].run_number == 9

        # wrong instrument
        rst, count, filtered_count = get_run_list_newest(0, 10, "testinst_wrong", "", "", "")
        assert count == 10
        assert filtered_count == 0
        assert len(rst) == 0

        # run number
        rst, count, filtered_count = get_run_list_newest(0, 10, "", "2", "", "")
        assert count == 10
        assert filtered_count == 1
        assert rst[0].run_number == 2

        # date, old date should return nothing
        rst, count, filtered_count = get_run_list_newest(0, 10, "", "", "1900-01-01", "")
        assert count == 10
        assert filtered_count == 0
        assert len(rst) == 0

        # date, todays date should return all
        rst, count, filtered_count = get_run_list_newest(0, 10, "", "", str(datetime.date.today()), "")
        assert count == 10
        assert filtered_count == 10
        assert rst[0].run_number == 9

        # complete status
        rst, count, filtered_count = get_run_list_newest(0, 10, "", "", "", "complete")
        assert count == 10
        assert filtered_count == 5
        assert rst[0].run_number == 8

        # error status
        rst, count, filtered_count = get_run_list_newest(0, 10, "", "", "", "error")
        assert count == 10
        assert filtered_count == 1
        assert rst[0].run_number == 7

        # incomplete status
        rst, count, filtered_count = get_run_list_newest(0, 10, "", "", "", "incomplete")
        assert count == 10
        assert filtered_count == 2
        assert rst[0].run_number == 9

        # acquiring status
        rst, count, filtered_count = get_run_list_newest(0, 10, "", "", "", "acquiring")
        assert count == 10
        assert filtered_count == 2
        assert rst[0].run_number == 3

    def test_get_signals(self):
        from reporting.dasmon.view_util import get_signals

        # make signals
        inst = Instrument.objects.create(name="testinst_getsignals")
        inst.save()
        for i in range(4):
            sig = Signal(
                instrument_id=inst,
                name=f"sig_{i}",
                source=f"src_{i}",
                message=f"msg_{i}",
                level=i,
                timestamp=timezone.now(),
            )
            sig.save()
        # test
        sig_list = get_signals(inst)
        for i, me in enumerate(sig_list):
            assert me.name == f"sig_{i}"
            assert f"msg_{i}" in me.status

    def test_get_instrument_status_summary(self):
        from reporting.dasmon.view_util import get_instrument_status_summary

        # make instrument
        # NOTE: using the class level inst to make life easier
        # test
        instrument_list = get_instrument_status_summary()
        print(instrument_list)
        # [
        # {'name': 'common',
        #  'recording_status': 'Unknown',
        #  'url': '/dasmon/common/',
        #  'diagnostics_url': '/dasmon/common/diagnostics/',
        #  'dasmon_status': 2,
        #  'pvstreamer_status': 2},
        # {'name': 'testinst',
        #  'recording_status': 'Unknown',
        #  'url': '/dasmon/testinst/',
        #  'diagnostics_url': '/dasmon/testinst/diagnostics/',
        #  'dasmon_status': 2,
        #  'pvstreamer_status': 2}
        # ]
        for me in instrument_list:
            assert me["recording_status"] == "Unknown"
            assert me["url"] == f"/dasmon/{me['name']}/"
            assert me["diagnostics_url"] == f"/dasmon/{me['name']}/diagnostics/"
            assert me["dasmon_status"] == -1
            assert me["pvstreamer_status"] == -1

    def test_get_dashboard_data(self):
        from reporting.dasmon.view_util import get_dashboard_data

        # make entries
        # NOTE: using the two inst defined for the class
        # test
        data_dict = get_dashboard_data()
        # -- since the instrument are dummy ones, the rate are just the default
        #    values of no real meaning
        assert "common" in data_dict.keys()
        assert "testinst" in data_dict.keys()

    def test_add_status_entry(self):
        from reporting.dasmon.view_util import add_status_entry

        # setup
        inst = Instrument.objects.create(name="testinst_addstatus")
        inst.save()
        para = Parameter.objects.create(name="testpara_addstatus")
        para.save()
        StatusVariable(
            instrument_id=inst,
            key_id=para,
            value="init",
        )
        # test
        add_status_entry(inst, "testpara_addstatus", "updated")
        sv = StatusVariable.objects.filter(instrument_id=inst, key_id=para).latest("timestamp")
        assert sv.value == "updated"

    def test_get_latest_updates(self):
        from reporting.dasmon.view_util import get_latest_updates

        # make entries
        inst = Instrument.objects.create(name="testinst_getlatestupdates")
        inst.save()
        para = Parameter.objects.create(name="testpara_getlatestupdates")
        para.save()
        for i in range(10):
            sv = StatusVariable(
                instrument_id=inst,
                key_id=para,
                value=f"val_{i}",
            )
            sv.save()
        # test
        data = get_latest_updates(inst, "testpara_getlatestupdates")
        for i, d in enumerate(data):
            assert d["info"] == f"val_{i}"

    def test_get_instruments_for_user(self):
        from reporting.dasmon.view_util import get_instruments_for_user

        # make entries
        gp_name = "TESTINST" + settings.INSTRUMENT_TEAM_SUFFIX
        gp = Group.objects.create(name=gp_name)
        gp.save()
        # mock request
        request = mock.MagicMock()
        request.user.groups.all.return_value = [Group.objects.get(name=gp_name)]
        # test
        inst_list = get_instruments_for_user(request)
        assert inst_list[0] == "TESTINST"


if __name__ == "__main__":
    pytest.main([__file__])
