import pytest
import json

from django.test import TestCase

from workflow.database import transactions
from workflow.database.report.models import (
    DataRun,
    Instrument,
    IPTS,
    RunStatus,
    StatusQueue,
    Task,
    WorkflowSummary,
)


class TransactionsTest(TestCase):

    data_dict = {
        "instrument": "HYSA",
        "facility": "SNS",
        "ipts": "IPTS-5678",
        "run_number": "1234",
        "data_file": "",
        "information": "test information msg",
        "error": "test error msg",
    }

    headers = {
        "expires": "0",
        "timestamp": "1344613053723",
        "destination": "/queue/POSTPROCESS.DATA_READY",
        "persistent": "true",
        "priority": "5",
        "message-id": "ID",
    }

    def test_add_status_entry(self):
        transactions.add_status_entry(self.headers, json.dumps(self.data_dict))

        self.assertEqual(len(Instrument.objects.get_queryset()), 1)
        instr_id = Instrument.objects.get_queryset()[0]
        self.assertEqual(instr_id.name, self.data_dict["instrument"].lower())
        self.assertEqual(instr_id.number_of_runs(), 1)
        self.assertEqual(instr_id.number_of_expts(), 1)

        self.assertEqual(len(IPTS.objects.get_queryset()), 1)
        ipts_id = IPTS.objects.get_queryset()[0]
        self.assertEqual(ipts_id.expt_name, self.data_dict["ipts"])
        self.assertEqual(len(ipts_id.instruments.get_queryset()), 1)
        self.assertEqual(ipts_id.instruments.get_queryset()[0], instr_id)

        self.assertEqual(len(DataRun.objects.get_queryset()), 1)
        run_id = DataRun.objects.get_queryset()[0]
        self.assertEqual(run_id.run_number, 1234)
        self.assertEqual(run_id.ipts_id, ipts_id)

        self.assertEqual(len(WorkflowSummary.objects.get_queryset()), 1)
        summary_id = WorkflowSummary.objects.get(run_id=run_id)
        self.assertFalse(summary_id.complete)

        self.assertEqual(len(RunStatus.objects.get_queryset()), 1)
        runstatus = RunStatus.objects.get_queryset()[0]

        self.assertIsNotNone(runstatus.last_info())
        self.assertEqual(runstatus.last_info().description, self.data_dict["information"])

        self.assertIsNotNone(runstatus.last_error())
        self.assertEqual(runstatus.last_error().description, self.data_dict["error"])

    def test_get_task(self):
        # test getting task without instrument
        task = transactions.get_task(self.headers, json.dumps(self.data_dict))
        self.assertIsNone(task)

        # getting task without any header
        task = transactions.get_task({}, json.dumps(self.data_dict))
        self.assertIsNone(task)

        # getting task with non-json data dict
        task = transactions.get_task(self.headers, self.data_dict)
        self.assertIsNone(task)

        # create testing instrument and task
        instr = Instrument.objects.create(name="hysa")
        instr.save()
        status_queue = StatusQueue(name="POSTPROCESS.DATA_READY")
        status_queue.save()
        transactions.add_task("hysa", "POSTPROCESS.DATA_READY")
        self.assertEqual(len(Task.objects.all()), 1)

        task = transactions.get_task(self.headers, json.dumps(self.data_dict))
        self.assertIsNotNone(task)
        task = json.loads(task)
        self.assertEqual(task["instrument"], "hysa")
        self.assertEqual(task["input_queue"], "POSTPROCESS.DATA_READY")

    def test_get_message_queues(self):
        status_id = StatusQueue(name="POSTPROCESS.DATA_READY", is_workflow_input=True)
        status_id.save()

        header = dict(self.headers)
        transactions.add_status_entry(header, json.dumps(self.data_dict))

        header["destination"] = "OTHER"
        transactions.add_status_entry(header, json.dumps(self.data_dict))

        # should return all queue names
        queues = transactions.get_message_queues(False)
        self.assertEqual(len(queues), 2)

        # should only return the first queue that was marked as a workflow input
        queues = transactions.get_message_queues(True)
        self.assertEqual(len(queues), 1)

    def test_add_task(self):
        # instrument does not exist, so task should not get added
        transactions.add_task("instr", "POSTPROCESS.DATA_READY")
        self.assertEqual(len(Task.objects.all()), 0)

        instr = Instrument.objects.create(name="hysa")
        instr.save()

        # task does not get made - valid instrument but queue does not exist yet
        transactions.add_task("hysa", "POSTPROCESS.DATA_READY")
        self.assertEqual(len(Task.objects.all()), 0)

        status_queue = StatusQueue(name="POSTPROCESS.DATA_READY")
        status_queue.save()

        # valid instrument and input queue
        transactions.add_task("hysa", "POSTPROCESS.DATA_READY")
        self.assertEqual(len(Task.objects.all()), 1)

        self.assertEqual(len(Task.objects.get_queryset()), 1)
        task = Task.objects.get_queryset()[0]
        self.assertEqual(task.instrument_id, instr)
        self.assertEqual(task.input_queue_id, status_queue)


if __name__ == "__main__":
    pytest.main()
