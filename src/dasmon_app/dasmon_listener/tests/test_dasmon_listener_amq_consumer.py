import unittest.mock as mock

import pytest
from dasmon_listener.amq_consumer import Client, Listener, store_and_cache_
from django.test import TestCase
from django.utils import timezone
from reporting.pvmon.models import PV, MonitoredVariable, PVCache, PVName, PVStringCache
from reporting.report.models import Instrument

values = {"test_key": "test_value"}


class TestAMQConsumer(TestCase):
    def get_listener(self):
        with mock.patch("workflow.database.report.models.Instrument.objects") as instrumentMock:  # noqa: F841
            with mock.patch("reporting.dasmon.models.Parameter.objects") as parameterMock:  # noqa: F841
                listener = Listener()
                return listener

    def get_client(self):
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

    def test_listen_and_wait(self):
        client = self.get_client()  # noqa: F841
        client._connection = mock.MagicMock()
        client._connection.is_connected = mock.MagicMock(return_value=True)

        inst = Instrument.objects.create(name="testinst")
        inst.save()
        pvname1 = PVName.objects.create(name="testpv1")
        pvname1.save()
        pvname2 = PVName.objects.create(name="testpv2")
        pvname2.save()
        stringpvname1 = PVName.objects.create(name="teststringpv1")
        stringpvname1.save()
        stringpvname2 = PVName.objects.create(name="teststringpv2")
        stringpvname2.save()

        really_old = timezone.now() - timezone.timedelta(days=365)  # 1 year old

        # This PV should not be purged because it is not old enough
        PV.objects.create(
            instrument=inst,
            name=pvname1,
            value=1.0,
            status=0,
            timestamp=timezone.now(),
        )
        # This PV should be purged because it is old enough
        PV.objects.create(
            instrument=inst,
            name=pvname1,
            value=2.0,
            status=0,
            timestamp=really_old,
        )
        # This PVCache should not be purged because it is a MonitoredVariable
        PVCache.objects.create(
            instrument=inst,
            name=pvname1,
            value=1.0,
            status=0,
            timestamp=really_old,
        )
        MonitoredVariable.objects.create(
            instrument=inst,
            pv_name=pvname1,
            rule_name="",
        )
        # This PVCache should be purged because it is old enough and not a MonitoredVariable
        PVCache.objects.create(
            instrument=inst,
            name=pvname2,
            value=1.0,
            status=0,
            timestamp=really_old,
        )

        # This PVStringCache should not be purged because it is a MonitoredVariable
        PVStringCache.objects.create(
            instrument=inst,
            name=stringpvname1,
            value="test",
            status=0,
            timestamp=really_old,
        )
        MonitoredVariable.objects.create(
            instrument=inst,
            pv_name=stringpvname1,
            rule_name="",
        )
        # This PVStringCache should be purged because it is old enough and not a Mon
        PVStringCache.objects.create(
            instrument=inst,
            name=stringpvname2,
            value="test",
            status=0,
            timestamp=really_old,
        )

        assert PV.objects.count() == 2
        assert PVCache.objects.count() == 2
        assert PVStringCache.objects.count() == 2

        client.listen_and_wait(repeat=False)

        assert PV.objects.count() == 1  # 1 PV should have been purged
        assert PVCache.objects.count() == 1  # 1 PVCache should have been purged
        assert PVCache.objects.first().name == pvname1  # PVName should be the same as the MonitoredVariable

        assert PVStringCache.objects.count() == 1  # 1 PVStringCache should have been purged
        assert PVStringCache.objects.first().name == stringpvname1  # PVName should be the same as the MonitoredVariable

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
