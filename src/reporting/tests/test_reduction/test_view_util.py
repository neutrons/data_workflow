from unittest import mock
from django.test import TestCase
from django.contrib.auth.models import User
from report.models import Instrument
from reduction.models import ReductionProperty, PropertyDefault
from reduction import view_util


class TestViewUtil(TestCase):
    @classmethod
    def setUpTestData(cls):
        inst = Instrument.objects.create(name="inst")
        inst.save()

        rp = ReductionProperty.objects.create(instrument=inst, key="key", value="value")
        PropertyDefault.objects.create(property=rp, value="default")

    @classmethod
    def classTearDown(cls):
        Instrument.objects.all().delete()

    def test_reduction_setup_urlr(self):
        response = view_util.reduction_setup_url("inst")
        self.assertEqual(response, None)

        response = view_util.reduction_setup_url("corelli")
        self.assertEqual(response, "/reduction/corelli/")

    def test_store_propertry(self):
        inst = Instrument.objects.get(name="inst")
        user = User.objects.create_user(username="user", password="password")

        # add new
        view_util.store_property(inst, "new_key", "new_value", user)
        rp = ReductionProperty.objects.get(id=2)
        self.assertEqual(rp.value, "new_value")

        # change existing
        view_util.store_property(inst, "new_key", "changed_value", user)
        rp = ReductionProperty.objects.get(id=2)
        self.assertEqual(rp.value, "changed_value")

        # add new entry with same key, nothing should be changed
        ReductionProperty.objects.create(
            instrument=inst, key="new_key", value="new_value2"
        )
        view_util.store_property(inst, "new_key", "new_value3", user)

        rp = ReductionProperty.objects.filter(instrument=inst, key="new_key")
        self.assertEqual(len(rp), 2)
        self.assertEqual(rp[0].value, "changed_value")
        self.assertEqual(rp[1].value, "new_value2")

    def test_reset_to_default(self):
        inst = Instrument.objects.get(name="inst")

        rp = ReductionProperty.objects.get(id=1)
        self.assertEqual(rp.value, "value")

        view_util.reset_to_default(inst)

        rp = ReductionProperty.objects.get(id=1)
        self.assertEqual(rp.value, "default")

    @mock.patch("dasmon.view_util.add_status_entry")
    @mock.patch("reporting_app.view_util.send_activemq_message")
    def test_send_template_request(self, mock_activemq, mock_dasmon_entry):
        inst = Instrument.objects.get(name="inst")

        view_util.send_template_request(
            inst, {"input1": "value1", "input2": 2, "use_default": True}
        )

        mock_activemq.assert_called_with(
            "/queue/REDUCTION.CREATE_SCRIPT",
            '{"instrument": "INST", "use_default": true, '
            '"template_data": {"input1": "value1", "input2": 2, "use_default": true}, '
            '"information": "Requested by unknown"}',
        )

        mock_dasmon_entry.assert_called_with(
            inst, "system_postprocessing", "Script requested by unknown"
        )

        view_util.send_template_request(
            inst, {"input1": "value1", "input2": 2, "use_default": "false"}
        )

        mock_activemq.assert_called_with(
            "/queue/REDUCTION.CREATE_SCRIPT",
            '{"instrument": "INST", "use_default": false, '
            '"template_data": {"input1": "value1", "input2": 2, "use_default": "false"}, '
            '"information": "Requested by unknown"}',
        )

        mock_dasmon_entry.assert_called_with(
            inst, "system_postprocessing", "Script requested by unknown"
        )
