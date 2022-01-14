import pytest
from unittest import TestCase
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

    def test_call(self):
        # NOTE: the decorator logged_action is preventing unittest mock from
        #       isolating the functionality for unit test, hence skipping
        pass

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
