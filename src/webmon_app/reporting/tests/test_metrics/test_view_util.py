from django.test import TestCase

from django.conf import settings
from django.utils import timezone

from reporting.report.models import Instrument, Information, RunStatus, StatusQueue, WorkflowSummary, Error
from reporting.dasmon.models import ActiveInstrument, Parameter, StatusCache
from workflow.database.report.models import DataRun
from workflow.database.report.models import IPTS


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
        recording = Parameter.objects.create(name="recording")
        recording.save()
        paused = Parameter.objects.create(name="paused")
        paused.save()
        StatusCache.objects.create(
            instrument_id=inst,
            key_id=recording,
            value="true",
        )
        StatusCache.objects.create(
            instrument_id=inst,
            key_id=paused,
            value="false",
        )

        # add common services
        common = Instrument.objects.create(name="common")
        common.save()
        ActiveInstrument.objects.create(
            instrument_id=common,
            is_alive=False,
            is_adara=False,
            has_pvsd=False,
            has_pvstreamer=False,
        )

    @classmethod
    def tearDownClass(cls):
        Instrument.objects.all().delete()
        Parameter.objects.all().delete()

    def test_postprocessing_diagnostics(self):
        from reporting.metrics.view_util import postprocessing_diagnostics

        # add postprocessing services
        common = Instrument.objects.get(name="common")
        for i in range(1, 3):
            name_postprocessor = settings.SYSTEM_STATUS_PREFIX + f"autoreducer{i}.com"
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
        info = Information(run_status_id=runStatus, description="autoreducer1.com")
        info.save()

        diag = postprocessing_diagnostics()
        node1 = diag[0]
        assert node1["name"] == "autoreducer1.com"
        assert node1["PID"] == "7"
        assert "timestamp" in node1
        assert "last_message_timestamp" in node1
        assert node1["last_message"] == "testinst_42: REDUCTION.COMPLETE"
        node2 = diag[1]
        assert node2["name"] == "autoreducer2.com"
        assert node2["PID"] == "7"
        assert "timestamp" in node2
        assert "last_message_timestamp" not in node2
        assert "last_message" not in node2

    def test_instrument_status(self):
        from reporting.metrics.view_util import instrument_status

        assert instrument_status() == {"testinst": "Recording"}

    def test_run_statuses(self):
        from reporting.metrics.view_util import run_statuses

        inst = Instrument.objects.get(name="testinst")
        ipts = IPTS(expt_name="IPTS-13")
        ipts.save()

        queue = StatusQueue(name="POSTPROCESS.DATA_READY")
        queue.save()

        # run too old, should not be included in output
        dataRun0 = DataRun(run_number=0, ipts_id=ipts, instrument_id=inst, file="/filename")
        dataRun0.save()  # need to save once so auto time can be written first so we can override
        dataRun0.created_on = timezone.now() - timezone.timedelta(minutes=120)
        dataRun0.save()
        RunStatus(run_id=dataRun0, queue_id=queue).save()
        WorkflowSummary.objects.create(run_id=dataRun0, complete=True)

        statuses = run_statuses()
        assert statuses["count"] == 0
        assert statuses["acquiring"] == 0
        assert statuses["incomplete"] == 0
        assert statuses["complete"] == 0
        assert statuses["error"] == 0

        # run should be acquiring
        dataRun1 = DataRun(run_number=1, ipts_id=ipts, instrument_id=inst, file="/filename")
        dataRun1.save()
        WorkflowSummary.objects.create(run_id=dataRun1)

        statuses = run_statuses()
        assert statuses["count"] == 1
        assert statuses["acquiring"] == 1
        assert statuses["incomplete"] == 0
        assert statuses["complete"] == 0
        assert statuses["error"] == 0

        # run should be incomplete
        dataRun2 = DataRun(run_number=2, ipts_id=ipts, instrument_id=inst, file="/filename")
        dataRun2.save()
        RunStatus(run_id=dataRun2, queue_id=queue).save()
        WorkflowSummary.objects.create(run_id=dataRun2)

        statuses = run_statuses()
        assert statuses["count"] == 2
        assert statuses["acquiring"] == 1
        assert statuses["incomplete"] == 1
        assert statuses["complete"] == 0
        assert statuses["error"] == 0

        # run should be complete
        dataRun3 = DataRun(run_number=3, ipts_id=ipts, instrument_id=inst, file="/filename")
        dataRun3.save()
        RunStatus(run_id=dataRun3, queue_id=queue).save()
        WorkflowSummary.objects.create(run_id=dataRun3, complete=True)

        statuses = run_statuses()
        assert statuses["count"] == 3
        assert statuses["acquiring"] == 1
        assert statuses["incomplete"] == 1
        assert statuses["complete"] == 1
        assert statuses["error"] == 0

        # run should be error
        dataRun4 = DataRun(run_number=4, ipts_id=ipts, instrument_id=inst, file="/filename")
        dataRun4.save()
        runStatus = RunStatus(run_id=dataRun4, queue_id=queue)
        runStatus.save()
        Error(run_status_id=runStatus, description="error").save()
        WorkflowSummary.objects.create(run_id=dataRun4)

        statuses = run_statuses()
        assert statuses["count"] == 4
        assert statuses["acquiring"] == 1
        assert statuses["incomplete"] == 1
        assert statuses["complete"] == 1
        assert statuses["error"] == 1
