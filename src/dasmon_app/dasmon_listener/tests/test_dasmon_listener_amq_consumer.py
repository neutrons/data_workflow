from dasmon_listener.amq_consumer import Listener, Client, store_and_cache_

import unittest.mock as mock
from django.test import TestCase
import pytest

values = {"test_key": "test_value"}


class TestAMQConsumer(TestCase):
    def get_listener(self):
        with mock.patch("workflow.database.report.models.Instrument.objects") as instrumentMock:  # noqa: F841
            with mock.patch("reporting.dasmon.models.Parameter.objects") as parameterMock:  # noqa: F841
                listener = Listener()
                return listener

    def get_client(self):
        with mock.patch("workflow.database.report.models.Instrument.objects") as instrumentMock:  # noqa: F841
            client = Client(None, None, None)
            return client

    @mock.patch("reporting.dasmon.models.Parameter.save")
    def test_retrieve_parameter_no_exist(self, parametereSaveMock):
        listener = self.get_listener()
        self.assertEqual(str(listener.retrieve_parameter("test_key")), "test_key")
        parametereSaveMock.assert_called()

    @mock.patch("workflow.database.report.models.Instrument.save")
    def test_retrieve_instrument_no_exist(self, instrumentSaveMock):
        listener = self.get_listener()
        self.assertEqual(str(listener.retrieve_instrument("test_key")), "test_key")
        instrumentSaveMock.assert_called()

    # need to make variations on this test to go down all the branches of this function
    @mock.patch("reporting.dasmon.models.Parameter.save")
    @mock.patch("workflow.database.report.models.Instrument.save")
    @mock.patch("dasmon_listener.amq_consumer.store_and_cache_")
    @mock.patch("dasmon_listener.amq_consumer.process_ack")
    @mock.patch("json.loads")
    def test_on_message_status_sts(
        self,
        jsonLoadsMock,
        processAckMock,
        storeAncCacheMock,
        instrumentSaveMock,
        parametereSaveMock,
    ):
        listener = self.get_listener()
        frame = mock.Mock()
        # ending with .ACK returns premptively
        frame.headers = {"header1": "header1_value", "destination": "STATUS.STS"}
        frame.body = "body"
        jsonLoadsMock.return_value = {"status": "cowboy2"}
        listener.on_message(frame)
        jsonLoadsMock.assert_called()
        storeAncCacheMock.assert_called()

    @mock.patch("reporting.dasmon.models.Parameter.save")
    @mock.patch("workflow.database.report.models.Instrument.save")
    @mock.patch("dasmon_listener.amq_consumer.store_and_cache_")
    @mock.patch("dasmon_listener.amq_consumer.process_ack")
    @mock.patch("json.loads")
    def test_on_message_status_stc(
        self,
        jsonLoadsMock,
        processAckMock,
        storeAncCacheMock,
        instrumentSaveMock,
        parametereSaveMock,
    ):
        listener = self.get_listener()
        frame = mock.Mock()
        # ending with .ACK returns premptively
        frame.headers = {"header1": "header1_value", "destination": "STATUS.STC"}
        frame.body = "body"
        jsonLoadsMock.return_value = {"status": "cowboy2"}
        listener.on_message(frame)
        jsonLoadsMock.assert_called()
        storeAncCacheMock.assert_called()

    @mock.patch("dasmon_listener.amq_consumer.process_ack")
    @mock.patch("json.loads")
    def test_on_message_process_ack(self, jsonLoadsMock, processAckMock):
        listener = self.get_listener()
        frame = mock.Mock()
        # ending with .ACK returns premptively
        frame.headers = {"header1": "header1_value", "destination": "STATUS.ACK"}
        frame.body = "body"
        jsonLoadsMock.return_value = {"status": "cowboy2"}
        listener.on_message(frame)
        jsonLoadsMock.assert_called()
        processAckMock.assert_called()

    @mock.patch("reporting.dasmon.models.Parameter.save")
    @mock.patch("workflow.database.report.models.Instrument.save")
    @mock.patch("dasmon_listener.amq_consumer.store_and_cache_")
    @mock.patch("dasmon_listener.amq_consumer.process_ack")
    @mock.patch("json.loads")
    def test_on_message_status_sms(
        self,
        jsonLoadsMock,
        processAckMock,
        storeAncCacheMock,
        instrumentSaveMock,
        parametereSaveMock,
    ):
        listener = self.get_listener()
        frame = mock.Mock()
        # ending with .ACK returns premptively
        frame.headers = {"header1": "header1_value", "destination": "STATUS.SMS"}
        frame.body = "body"
        jsonLoadsMock.return_value = {"status": "cowboy2"}
        listener.on_message(frame)
        jsonLoadsMock.assert_called()
        storeAncCacheMock.assert_called()

    @mock.patch("reporting.dasmon.models.Parameter.save")
    @mock.patch("workflow.database.report.models.Instrument.save")
    @mock.patch("dasmon_listener.amq_consumer.store_and_cache_")
    @mock.patch("dasmon_listener.amq_consumer.process_ack")
    @mock.patch("json.loads")
    def test_on_message_status_dict(
        self,
        jsonLoadsMock,
        processAckMock,
        storeAncCacheMock,
        instrumentSaveMock,
        parametereSaveMock,
    ):
        listener = self.get_listener()
        frame = mock.Mock()
        # ending with .ACK returns premptively
        frame.headers = {"header1": "header1_value", "destination": "STATUS."}
        frame.body = "body"
        jsonLoadsMock.return_value = {
            "status": "cowboy2",
            "src_id": "eels",
            "pid": "norman reedus",
        }
        listener.on_message(frame)
        jsonLoadsMock.assert_called()
        storeAncCacheMock.assert_called()

    @mock.patch("reporting.dasmon.models.Parameter.save")
    @mock.patch("workflow.database.report.models.Instrument.save")
    @mock.patch("dasmon_listener.amq_consumer.process_signal")
    @mock.patch("json.loads")
    def test_on_message_signal(self, jsonLoadsMock, processSignal, instrumentSaveMock, parametereSaveMock):
        listener = self.get_listener()
        frame = mock.Mock()
        # ending with .ACK returns premptively
        frame.headers = {"header1": "header1_value", "destination": "SIGNAL.STS"}
        frame.body = "body"
        jsonLoadsMock.return_value = {"status": "cowboy2"}
        listener.on_message(frame)
        jsonLoadsMock.assert_called()
        processSignal.assert_called()

    @mock.patch("reporting.dasmon.models.Parameter.save")
    @mock.patch("workflow.database.report.models.Instrument.save")
    @mock.patch("dasmon_listener.amq_consumer.process_SMS")
    @mock.patch("json.loads")
    def test_on_message_app_sms(self, jsonLoadsMock, processSMS, instrumentSaveMock, parametereSaveMock):
        listener = self.get_listener()
        frame = mock.Mock()
        # ending with .ACK returns premptively
        frame.headers = {"header1": "header1_value", "destination": "APP.SMS"}
        frame.body = "body"
        jsonLoadsMock.return_value = {"status": "cowboy2"}
        listener.on_message(frame)
        jsonLoadsMock.assert_called()
        processSMS.assert_called()

    @mock.patch("reporting.dasmon.models.Parameter.save")
    @mock.patch("workflow.database.report.models.Instrument.save")
    @mock.patch("dasmon_listener.amq_consumer.store_and_cache_")
    @mock.patch("json.loads")
    def test_on_message_status_else(self, jsonLoadsMock, storeAncCacheMock, instrumentSaveMock, parametereSaveMock):
        listener = self.get_listener()
        frame = mock.Mock()
        # ending with .ACK returns premptively
        frame.headers = {"header1": "header1_value", "destination": "ELSE"}
        frame.body = "body"
        jsonLoadsMock.return_value = {
            "status": "cowboy2",
            "monitors": {
                "item1": "item1",
                "dict1": {"id": "dict1_id", "counts": "dict1_counts"},
            },
        }
        listener.on_message(frame)
        jsonLoadsMock.assert_called()
        storeAncCacheMock.assert_called()

    @mock.patch("dasmon_listener.amq_consumer.Parameter.objects.get")
    def test_listen_and_wait(self, parameterMock):
        client = self.get_client()  # noqa: F841

    #   client.listen_and_wait()
    #   need to either refactor the code such that testable parts are
    #   in functions or not use a while true loop,
    #   else its kinda hard to test

    def test_store_and_cache_not_monitored(self):
        instrument_id = mock.MagicMock()

        key_id = mock.Mock()
        key_id.monitored = False

        value = mock.MagicMock()
        store_and_cache_(instrument_id, key_id, value)

    @mock.patch("dasmon_listener.amq_consumer.StatusCache")
    @mock.patch("dasmon_listener.amq_consumer.StatusVariable")
    def test_store_and_cache_str_len(self, statusVariableMock, statusCacheMock):
        statusVariableMock.save = mock.MagicMock()

        instrument_id = mock.MagicMock()

        key_id = mock.Mock()
        key_id.monitored = True

        value = (
            "the max string length is one-hundred and twenty eight, "
            + "this string should be longer than that and cause it to cut off the end of this sentence"  # noqa: W503
        )
        store_and_cache_(instrument_id, key_id, value, None, False)
        statusVariableMock.assert_called_with(
            instrument_id=instrument_id,
            key_id=key_id,
            value="the max string length is one-hundred and twenty eight,"
            + " this string should be longer than that and cause it to cut off the end of",  # noqa: W503
        )

        # called with valuestring of size 128

    @mock.patch("dasmon_listener.amq_consumer.StatusCache")
    @mock.patch("dasmon_listener.amq_consumer.StatusVariable")
    def test_store_and_cache_no_cache(self, statusVariableMock, statusCacheMock):
        statusVariableMock.save = mock.MagicMock()

        instrument_id = mock.MagicMock()

        key_id = mock.Mock()
        key_id.monitored = True

        value = (
            "the max string length is one-hundred and twenty eight,"
            + " this string should be longer than that and cause it to cut off the end of this sentence"  # noqa: W503
        )
        store_and_cache_(instrument_id, key_id, value, None, True)
        statusVariableMock.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__])
