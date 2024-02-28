import pytest
from django.test import TestCase
from unittest import mock
import workflow

_ = [workflow]


class StateActionTest(TestCase):
    def test_call_default_task(self):
        from workflow.states import StateAction

        sa = StateAction()
        headers = {"destination": "test"}
        message = "test_msg"
        sa._call_default_task(headers, message)

    def test_call_db_task(self):
        from workflow.states import StateAction

        sa = StateAction()
        # NOTE: it is unclear what is the task definition, so the only thing can
        #       be tested here is the null task def
        task_data = "{}"
        headers = {"destination": "test"}
        message = "test_msg"
        sa._call_db_task(task_data, headers, message)

    @mock.patch("workflow.states.transactions.get_task")
    def test_call(self, mock_get_task):
        # NOTE: skipping testing of importing a task class as this option is not currently used
        from workflow.states import StateAction

        mock_connection = mock.Mock()
        sa = StateAction(connection=mock_connection, use_db_task=True)
        headers = {"destination": "test", "message-id": "test-0"}
        message = '{"facility": "SNS", "instrument": "arcs", "ipts": "IPTS-5", "run_number": 3, "data_file": "test"}'

        # test with task class: null
        mock_get_task.return_value = '{"task_class": null, "task_queues": ["QUEUE-0", "QUEUE-1"]}'
        sa(headers, message)
        assert mock_connection.send.call_count == 2  # one per task queue
        original_call_count = mock_connection.send.call_count

        # test with task class: empty string
        mock_get_task.return_value = '{"task_class": "", "task_queues": ["QUEUE-0", "QUEUE-1"]}'
        sa(headers, message)
        assert mock_connection.send.call_count - original_call_count == 2  # one per task queue

    @mock.patch("workflow.database.transactions.add_status_entry")
    def test_send(self, mockAddStatusEntry):
        from workflow.states import StateAction

        add_status_entry = mock.MagicMock()
        mockAddStatusEntry = mock.MagicMock(return_value=add_status_entry)
        # case: send_connection is None
        POSTPROCESS_ERROR = "test"
        _ = [mockAddStatusEntry, POSTPROCESS_ERROR]
        message = "{}"
        sa = StateAction()
        sa.send("test", message)
        # case: send_connection is not None
        sa = StateAction(connection=mock.Mock())
        sa.send("test", message)


class PostProcessDataReadyTest(TestCase):
    def test_call(self):
        from workflow.states import Postprocess_data_ready

        pdr = Postprocess_data_ready()
        mock_send = mock.MagicMock()
        pdr.send = mock_send
        pdr("test", "test")
        mock_send.assert_called()


class ReductionRequestTest(TestCase):
    def test_call(self):
        from workflow.states import Reduction_request

        rr = Reduction_request()
        mock_send = mock.MagicMock()
        rr.send = mock_send
        rr("test", "test")
        mock_send.assert_called()


class CatalogRequestTest(TestCase):
    def test_call(self):
        from workflow.states import Catalog_request

        cr = Catalog_request()
        mock_send = mock.MagicMock()
        cr.send = mock_send
        cr("test", "test")
        mock_send.assert_called()


class ReductionCompleteTest(TestCase):
    def test_call(self):
        from workflow.states import Reduction_complete

        rc = Reduction_complete()
        mock_send = mock.MagicMock()
        rc.send = mock_send
        rc("test", "test")
        mock_send.assert_called()


if __name__ == "__main__":
    pytest.main()
