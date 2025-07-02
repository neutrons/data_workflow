from unittest import mock

import pytest
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.test import TestCase
from django.urls import reverse
from workflow.database.report.models import StatusQueue

from reporting import report
from reporting.dasmon.models import ActiveInstrument
from reporting.report.models import IPTS, DataRun, Instrument, RunStatus

_ = [report]


class SummaryViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create user
        User.objects.create_superuser(username="testuser", password="12345").save()
        # Create instrument
        inst = Instrument.objects.create(name="test_instrument")
        inst.save()
        ActiveInstrument.objects.create(
            instrument_id=inst,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
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

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="TEST_IPTS").delete()
        StatusQueue.objects.get(name="TEST_QUEUE").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/report/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("report:summary"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("report:summary"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "report/global_summary.html")

    def test_response_content(self):
        response = self.client.get(reverse("report:summary"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"test_instrument" in response.content)


class ProcessingAdminViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create user
        User.objects.create_superuser(username="testuser", password="12345").save()
        # Create instrument
        inst = Instrument.objects.create(name="test_instrument")
        inst.save()
        ActiveInstrument.objects.create(
            instrument_id=inst,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
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

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="TEST_IPTS").delete()
        StatusQueue.objects.get(name="TEST_QUEUE").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/report/processing")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("report:processing_admin"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("report:processing_admin"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "report/processing_admin.html")

    def test_response_content(self):
        response = self.client.get(reverse("report:processing_admin"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"test_instrument" in response.content)


class InstrumentSummaryViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create user
        User.objects.create_superuser(username="testuser", password="12345").save()
        # Create instrument
        inst = Instrument.objects.create(name="test_instrument")
        inst.save()
        ActiveInstrument.objects.create(
            instrument_id=inst,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
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

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="TEST_IPTS").delete()
        StatusQueue.objects.get(name="TEST_QUEUE").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/report/test_instrument/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("report:instrument_summary", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("report:instrument_summary", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "report/instrument.html")

    def test_response_content(self):
        response = self.client.get(reverse("report:instrument_summary", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"test_instrument" in response.content)
        self.assertTrue("IPTS: TEST_IPTS", str(response.context))


class GetInstrumentUpdateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create user
        User.objects.create_superuser(username="testuser", password="12345").save()
        # Create instrument
        inst = Instrument.objects.create(name="test_instrument")
        inst.save()
        ActiveInstrument.objects.create(
            instrument_id=inst,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
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

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="TEST_IPTS").delete()
        StatusQueue.objects.get(name="TEST_QUEUE").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/report/test_instrument/update/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("report:get_instrument_update", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)


class DetailViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create user
        User.objects.create_superuser(username="testuser", password="12345").save()
        # Create instrument
        inst = Instrument.objects.create(name="test_instrument")
        inst.save()
        ActiveInstrument.objects.create(
            instrument_id=inst,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
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

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="TEST_IPTS").delete()
        StatusQueue.objects.get(name="TEST_QUEUE").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/report/test_instrument/1/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("report:detail", args=["test_instrument", 1]))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("report:detail", args=["test_instrument", 1]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "report/detail.html")

    def test_response_content(self):
        response = self.client.get(reverse("report:detail", args=["test_instrument", 1]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"test_instrument" in response.content)


class DownloadReducedDataViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create user
        User.objects.create_superuser(username="testuser", password="12345").save()
        # Create instrument
        inst = Instrument.objects.create(name="test_instrument")
        inst.save()
        ActiveInstrument.objects.create(
            instrument_id=inst,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
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

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="TEST_IPTS").delete()
        StatusQueue.objects.get(name="TEST_QUEUE").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location_no_reduced_data(self):
        response = self.client.get("/report/test_instrument/1/data/")
        self.assertEqual(response.status_code, 404)

    @mock.patch("reporting.report.view_util.extract_ascii_from_div")
    def test_view_url_exists_at_desired_location_has_reduced_data(self, mockExtract):
        # Without patching, we will get a 404 by default
        mockExtract.return_value = "1.09844 32.9007 0 0\n1.09932 33.8835 0 0\n1.1002 34.963 0 0\n"
        response = self.client.get("/report/test_instrument/1/data/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name_no_reduced_data(self):
        response = self.client.get(reverse("report:download_reduced_data", args=["test_instrument", 1]))
        self.assertEqual(response.status_code, 404)

    @mock.patch("reporting.report.view_util.extract_ascii_from_div")
    def test_view_url_accessible_by_name_has_reduced_data(self, mockExtract):
        mockExtract.return_value = "1.09844 32.9007 0 0\n1.09932 33.8835 0 0\n1.1002 34.963 0 0\n"
        response = self.client.get(reverse("report:download_reduced_data", args=["test_instrument", 1]))
        self.assertEqual(response.status_code, 200)


class SubmitForReductionViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create user
        User.objects.create_superuser(username="testuser", password="12345").save()
        # Create instrument
        inst = Instrument.objects.create(name="test_instrument")
        inst.save()
        ActiveInstrument.objects.create(
            instrument_id=inst,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
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

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="TEST_IPTS").delete()
        StatusQueue.objects.get(name="TEST_QUEUE").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    @mock.patch("reporting.report.view_util.processing_request")
    def test_view_url_exists_at_desired_location(self, mockProcessingRequest):
        mockProcessingRequest.return_value = redirect(reverse("report:detail", args=["test_instrument", 1]))
        response = self.client.get("/report/test_instrument/1/reduce/")
        # NOTE: this is either fail or redirect
        self.assertEqual(response.status_code, 302)

    @mock.patch("reporting.report.view_util.processing_request")
    def test_view_url_accessible_by_name(self, mockProcessingRequest):
        mockProcessingRequest.return_value = redirect(reverse("report:detail", args=["test_instrument", 1]))
        response = self.client.get(reverse("report:submit_for_reduction", args=["test_instrument", 1]))
        self.assertEqual(response.status_code, 302)


class SubmitForCatalogViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create user
        User.objects.create_superuser(username="testuser", password="12345").save()
        # Create instrument
        inst = Instrument.objects.create(name="test_instrument")
        inst.save()
        ActiveInstrument.objects.create(
            instrument_id=inst,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
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

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="TEST_IPTS").delete()
        StatusQueue.objects.get(name="TEST_QUEUE").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    @mock.patch("reporting.report.view_util.processing_request")
    def test_view_url_exists_at_desired_location(self, mockProcessingRequest):
        mockProcessingRequest.return_value = redirect(reverse("report:detail", args=["test_instrument", 1]))
        response = self.client.get("/report/test_instrument/1/catalog/")
        # NOTE: this is either fail or redirect
        self.assertEqual(response.status_code, 302)

    @mock.patch("reporting.report.view_util.processing_request")
    def test_view_url_accessible_by_name(self, mockProcessingRequest):
        mockProcessingRequest.return_value = redirect(reverse("report:detail", args=["test_instrument", 1]))
        response = self.client.get(reverse("report:submit_for_cataloging", args=["test_instrument", 1]))
        self.assertEqual(response.status_code, 302)


class SubmitForPostProcessingViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create user
        User.objects.create_superuser(username="testuser", password="12345").save()
        # Create instrument
        inst = Instrument.objects.create(name="test_instrument")
        inst.save()
        ActiveInstrument.objects.create(
            instrument_id=inst,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
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

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="TEST_IPTS").delete()
        StatusQueue.objects.get(name="TEST_QUEUE").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    @mock.patch("reporting.report.view_util.processing_request")
    def test_view_url_exists_at_desired_location(self, mockProcessingRequest):
        mockProcessingRequest.return_value = redirect(reverse("report:detail", args=["test_instrument", 1]))
        response = self.client.get("/report/test_instrument/1/postprocess/")
        # NOTE: this is either fail or redirect
        self.assertEqual(response.status_code, 302)

    @mock.patch("reporting.report.view_util.processing_request")
    def test_view_url_accessible_by_name(self, mockProcessingRequest):
        mockProcessingRequest.return_value = redirect(reverse("report:detail", args=["test_instrument", 1]))
        response = self.client.get(reverse("report:submit_for_post_processing", args=["test_instrument", 1]))
        self.assertEqual(response.status_code, 302)


class GetExperimentUpdateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create user
        User.objects.create_superuser(username="testuser", password="12345").save()
        # Create instrument
        inst = Instrument.objects.create(name="test_instrument")
        inst.save()
        ActiveInstrument.objects.create(
            instrument_id=inst,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
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

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="TEST_IPTS").delete()
        StatusQueue.objects.get(name="TEST_QUEUE").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/report/test_instrument/experiment/TEST_IPTS/update/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("report:get_experiment_update", args=["test_instrument", "TEST_IPTS"]))
        self.assertEqual(response.status_code, 200)


class IPTSSummaryViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create user
        User.objects.create_superuser(username="testuser", password="12345").save()
        # Create instrument
        inst = Instrument.objects.create(name="test_instrument")
        inst.save()
        ActiveInstrument.objects.create(
            instrument_id=inst,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
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

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="TEST_IPTS").delete()
        StatusQueue.objects.get(name="TEST_QUEUE").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/report/test_instrument/experiment/TEST_IPTS/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("report:ipts_summary", args=["test_instrument", "TEST_IPTS"]))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("report:ipts_summary", args=["test_instrument", "TEST_IPTS"]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "report/ipts_summary.html")

    def test_list_content(self):
        response = self.client.get(reverse("report:ipts_summary", args=["test_instrument", "TEST_IPTS"]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue("TEST_INSTRUMENT" in str(response.context))
        self.assertTrue("TEST_IPTS" in str(response.context))


class LiveErrorsViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create user
        User.objects.create_superuser(username="testuser", password="12345").save()
        # Create instrument
        inst = Instrument.objects.create(name="test_instrument")
        inst.save()
        ActiveInstrument.objects.create(
            instrument_id=inst,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
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

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="TEST_IPTS").delete()
        StatusQueue.objects.get(name="TEST_QUEUE").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/report/test_instrument/errors/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("report:live_errors", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("report:live_errors", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "report/live_errors.html")

    def test_list_content(self):
        response = self.client.get(reverse("report:live_errors", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue("TEST_INSTRUMENT" in str(response.context))
        self.assertTrue("TEST_IPTS" in str(response.context))


class GetErrorUpdateViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create user
        User.objects.create_superuser(username="testuser", password="12345").save()
        # Create instrument
        inst = Instrument.objects.create(name="test_instrument")
        inst.save()
        ActiveInstrument.objects.create(
            instrument_id=inst,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
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

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="TEST_IPTS").delete()
        StatusQueue.objects.get(name="TEST_QUEUE").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/report/test_instrument/errors/update")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("report:get_error_update", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    pytest.main([__file__])
