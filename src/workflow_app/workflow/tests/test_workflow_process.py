import pytest
from unittest import mock
from django.test import TestCase
from reporting.report.models import DataRun
from reporting.report.models import IPTS
from reporting.report.models import Instrument
from reporting.report.models import RunStatus
from workflow.database.report.models import StatusQueue
from workflow.database.report.models import WorkflowSummary
import workflow

_ = [workflow]


class WorkflowProcessTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create instrument
        inst = Instrument.objects.create(name="test_instrument")
        inst.save()
        # Create IPTS
        ipts = IPTS.objects.create(expt_name="TEST_IPTS")
        ipts.save()
        ipts.instruments.add(inst)
        # Create StatusQueue
        sq = StatusQueue.objects.create(name="TEST_QUEUE", is_workflow_input=True)
        sq.save()
        # Create DataRun
        dr = DataRun.objects.create(
            run_number=1,
            ipts_id=ipts,
            instrument_id=inst,
            file="tmp/test.nxs.h5",
        )
        dr.save()
        # Create RunStatus
        rs = RunStatus.objects.create(
            run_id=dr,
            queue_id=sq,
            message_id="test_msg",
        )
        rs.save()
        WorkflowSummary.objects.create(
            run_id=dr,
            complete=True,
            catalog_started=True,
            cataloged=False,
            reduction_needed=True,
            reduction_started=True,
            reduced=True,
            reduction_cataloged=True,
            reduction_catalog_started=True,
        ).save()

    @classmethod
    def tearDownClass(cls):
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="TEST_IPTS").delete()
        StatusQueue.objects.get(name="TEST_QUEUE").delete()

    def test_call(self):
        from workflow.workflow_process import WorkflowProcess

        wfp = WorkflowProcess()
        mockVerify = mock.MagicMock()
        wfp.verify_workflow = mockVerify
        wfp()
        mockVerify.assert_called()

    @mock.patch("workflow.database.transactions")
    def test_verify_workflow(self, mockTransactions):
        from workflow.workflow_process import WorkflowProcess

        wfp = WorkflowProcess()
        wfp.verify_workflow()


if __name__ == "__main__":
    pytest.main()
