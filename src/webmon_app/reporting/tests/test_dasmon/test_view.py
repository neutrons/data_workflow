import pytest
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from workflow.database.report.models import IPTS, DataRun, WorkflowSummary

from reporting.dasmon.models import ActiveInstrument, Instrument
from reporting.pvmon.models import MonitoredVariable, PVCache, PVName


class DashboardViewTest(TestCase):
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

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/dasmon/dashboard/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("dasmon:dashboard"))
        self.assertEqual(response.status_code, 200)

    # somehow the default dashboard view is always updated to using
    # dashboard_simple instead.
    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("dasmon:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dasmon/dashboard_simple.html")

    def test_list_instrument(self):
        response = self.client.get(reverse("dasmon:dashboard"))
        self.assertEqual(response.status_code, 200)
        # NOTE: response is a dict of page, so the easiest way to check
        #       content is to cast it to a string
        self.assertTrue("test_instrument" in str(response.context))

    def test_dap_script_present_in_template(self):
        """Test that the Digital Analytics Program (DAP) script is present in the rendered template"""
        response = self.client.get(reverse("dasmon:dashboard"))
        self.assertEqual(response.status_code, 200)

        # Convert response content to string for searching
        response_content = response.content.decode("utf-8")

        # Check that DAP script elements are present in the rendered template
        self.assertIn("Digital Analytics Program (DAP)", response_content)
        self.assertIn("_fed_an_ua_tag", response_content)
        self.assertIn("dap.digitalgov.gov/Universal-Federated-Analytics-Min.js", response_content)
        self.assertIn("agency=DOE", response_content)
        self.assertIn("subagency=BES", response_content)
        self.assertIn("sitetopic=science", response_content)

        # Check that error handling is present
        self.assertIn("onerror", response_content)
        self.assertIn("DAP analytics script failed to load", response_content)


class DashboardSimpleViewTest(TestCase):
    # NOTE: DashboardSimple is an update of DashboardView
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

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/dasmon/dashboard/update/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("dasmon:dashboard_update"))
        self.assertEqual(response.status_code, 200)


class ExpertStatusViewTest(TestCase):
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

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/dasmon/expert/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("dasmon:diagnostics", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)

    # NOTE: despite the explicit definition of the view shows the template used to render
    #       the page is 'dasmon/expert_status.html', the actual template django used
    #       is 'dasmon/diagnostics.html'
    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("dasmon:diagnostics", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dasmon/diagnostics.html")

    def test_list_instrument(self):
        response = self.client.get(reverse("dasmon:diagnostics", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue("test_instrument" in str(response.context))


class RunSummaryViewTest(TestCase):
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
        # Create runs
        ipts = IPTS.objects.create(expt_name="ipts_test")
        ipts.save()
        for rn in range(4):
            run = DataRun.objects.create(
                run_number=rn,
                ipts_id=ipts,
                instrument_id=inst,
                file=f"/tmp/test_file_{rn}.nxs",
            )
            run.save()
            WorkflowSummary.objects.create(
                run_id=run,
                complete=True,
                catalog_started=True,
                cataloged=True,
                reduction_needed=True,
                reduction_started=True,
                reduced=True,
                reduction_cataloged=True,
                reduction_catalog_started=True,
            ).save()

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="ipts_test").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/dasmon/summary/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("dasmon:run_summary"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("dasmon:run_summary"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dasmon/run_summary.html")

    def test_list_run(self):
        response = self.client.get(reverse("dasmon:run_summary"))
        self.assertEqual(response.status_code, 200)


class RunSummaryUpdateViewTest(TestCase):
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
        # Create runs
        ipts = IPTS.objects.create(expt_name="ipts_test")
        ipts.save()
        for rn in range(4):
            run = DataRun.objects.create(
                run_number=rn,
                ipts_id=ipts,
                instrument_id=inst,
                file=f"/tmp/test_file_{rn}.nxs",
            )
            run.save()
            WorkflowSummary.objects.create(
                run_id=run,
                complete=True,
                catalog_started=True,
                cataloged=True,
                reduction_needed=True,
                reduction_started=True,
                reduced=True,
                reduction_cataloged=True,
                reduction_catalog_started=True,
            ).save()

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="ipts_test").delete()
        DataRun.objects.all().delete()
        WorkflowSummary.objects.all().delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/dasmon/summary/update/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("dasmon:run_summary_update"))
        self.assertEqual(response.status_code, 200)


class LiveMonitorViewTest(TestCase):
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
        # Create runs
        ipts = IPTS.objects.create(expt_name="ipts_test")
        ipts.save()
        for rn in range(4):
            run = DataRun.objects.create(
                run_number=rn,
                ipts_id=ipts,
                instrument_id=inst,
                file=f"/tmp/test_file_{rn}.nxs",
            )
            run.save()
            WorkflowSummary.objects.create(
                run_id=run,
                complete=True,
                catalog_started=True,
                cataloged=True,
                reduction_needed=True,
                reduction_started=True,
                reduced=True,
                reduction_cataloged=True,
                reduction_catalog_started=True,
            ).save()

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="ipts_test").delete()
        DataRun.objects.all().delete()
        WorkflowSummary.objects.all().delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/dasmon/test_instrument/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("dasmon:live_monitor", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("dasmon:live_monitor", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dasmon/live_monitor.html")

    def test_list_instrument(self):
        response = self.client.get(reverse("dasmon:live_monitor", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)
        assert "test_instrument" in str(response.context)

    def test_monitored_pv_table_placeholder_present(self):
        """The status page must provide the element the monitored PV table is loaded into"""
        response = self.client.get(reverse("dasmon:live_monitor", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)
        assert "monitored_pv_table" in response.content.decode()


class GetMonitoredPVTableViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="testuser", password="12345").save()
        inst = Instrument.objects.create(name="test_instrument")
        inst.save()
        ActiveInstrument.objects.create(
            instrument_id=inst,
            is_alive=True,
            is_adara=True,
            has_pvsd=True,
            has_pvstreamer=True,
        )
        pvname = PVName.objects.create(name="BeamPower")
        PVCache.objects.create(
            instrument=inst,
            name=pvname,
            value=1100.0,
            status=0,
            timestamp=timezone.now(),
        )
        MonitoredVariable.objects.create(instrument=inst, pv_name=pvname, rule_name="")

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        MonitoredVariable.objects.all().delete()
        PVCache.objects.all().delete()
        PVName.objects.all().delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/dasmon/test_instrument/monitored_pvs/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("dasmon:get_monitored_pv_table", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)

    def test_monitored_pv_is_rendered(self):
        response = self.client.get(reverse("dasmon:get_monitored_pv_table", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        assert "BeamPower" in content
        assert "1100" in content

    def test_unknown_instrument_does_not_render_a_table(self):
        # login_or_local_required_401 turns the Http404 into a 500, which is the
        # same behaviour as the other AJAX endpoints, e.g. dasmon:get_update
        response = self.client.get(reverse("dasmon:get_monitored_pv_table", args=["no_such_instrument"]))
        self.assertEqual(response.status_code, 500)


class LiveRunsViewTest(TestCase):
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
        # Create runs
        ipts = IPTS.objects.create(expt_name="ipts_test")
        ipts.save()
        for rn in range(4):
            run = DataRun.objects.create(
                run_number=rn,
                ipts_id=ipts,
                instrument_id=inst,
                file=f"/tmp/test_file_{rn}.nxs",
            )
            run.save()
            WorkflowSummary.objects.create(
                run_id=run,
                complete=True,
                catalog_started=True,
                cataloged=True,
                reduction_needed=True,
                reduction_started=True,
                reduced=True,
                reduction_cataloged=True,
                reduction_catalog_started=True,
            ).save()

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="ipts_test").delete()
        DataRun.objects.all().delete()
        WorkflowSummary.objects.all().delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/dasmon/test_instrument/runs/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("dasmon:live_runs", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("dasmon:live_runs", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dasmon/live_runs.html")

    def test_list_runs(self):
        response = self.client.get(reverse("dasmon:live_runs", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)
        assert "test_instrument" in str(response.context)


class UserHelpViewTest(TestCase):
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

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/dasmon/user_help/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("dasmon:user_help"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("dasmon:user_help"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dasmon/help.html")

    def test_list_user(self):
        response = self.client.get(reverse("dasmon:user_help"))
        self.assertEqual(response.status_code, 200)
        assert "testuser" in str(response.context)


class DiagnosticsViewTest(TestCase):
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
        # Create runs
        ipts = IPTS.objects.create(expt_name="ipts_test")
        ipts.save()
        for rn in range(4):
            run = DataRun.objects.create(
                run_number=rn,
                ipts_id=ipts,
                instrument_id=inst,
                file=f"/tmp/test_file_{rn}.nxs",
            )
            run.save()
            WorkflowSummary.objects.create(
                run_id=run,
                complete=True,
                catalog_started=True,
                cataloged=True,
                reduction_needed=True,
                reduction_started=True,
                reduced=True,
                reduction_cataloged=True,
                reduction_catalog_started=True,
            ).save()

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="ipts_test").delete()
        DataRun.objects.all().delete()
        WorkflowSummary.objects.all().delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/dasmon/test_instrument/diagnostics/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("dasmon:diagnostics", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("dasmon:diagnostics", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dasmon/diagnostics.html")

    def test_list_instrument(self):
        response = self.client.get(reverse("dasmon:diagnostics", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)
        assert "test_instrument" in str(response.context)
        assert "TEST_INSTRUMENT" in str(response.context)


class GetUpdateViewTest(TestCase):
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
        # Create runs
        ipts = IPTS.objects.create(expt_name="ipts_test")
        ipts.save()
        for rn in range(4):
            run = DataRun.objects.create(
                run_number=rn,
                ipts_id=ipts,
                instrument_id=inst,
                file=f"/tmp/test_file_{rn}.nxs",
            )
            run.save()
            WorkflowSummary.objects.create(
                run_id=run,
                complete=True,
                catalog_started=True,
                cataloged=True,
                reduction_needed=True,
                reduction_started=True,
                reduced=True,
                reduction_cataloged=True,
                reduction_catalog_started=True,
            ).save()

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="ipts_test").delete()
        DataRun.objects.all().delete()
        WorkflowSummary.objects.all().delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/dasmon/test_instrument/update/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("dasmon:get_update", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)


class SummaryUpdateTest(TestCase):
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
        # Create runs
        ipts = IPTS.objects.create(expt_name="ipts_test")
        ipts.save()
        for rn in range(4):
            run = DataRun.objects.create(
                run_number=rn,
                ipts_id=ipts,
                instrument_id=inst,
                file=f"/tmp/test_file_{rn}.nxs",
            )
            run.save()
            WorkflowSummary.objects.create(
                run_id=run,
                complete=True,
                catalog_started=True,
                cataloged=True,
                reduction_needed=True,
                reduction_started=True,
                reduced=True,
                reduction_cataloged=True,
                reduction_catalog_started=True,
            ).save()

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="ipts_test").delete()
        DataRun.objects.all().delete()
        WorkflowSummary.objects.all().delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/dasmon/update/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("dasmon:summary_update"))
        self.assertEqual(response.status_code, 200)

    def test_notifications_endpoint_returns_404(self):
        """Verify obsolete notifications endpoint returns 404"""
        response = self.client.get("/dasmon/notifications/")
        self.assertEqual(response.status_code, 404)

    def test_instrument_signals_endpoint_returns_404(self):
        """Verify obsolete signals endpoint returns 404"""
        response = self.client.get("/dasmon/test_instrument/signals/")
        self.assertEqual(response.status_code, 404)

    def test_acknowledge_signal_endpoint_returns_404(self):
        """Verify obsolete signal acknowledgment endpoint returns 404"""
        response = self.client.get("/dasmon/test_instrument/signals/ack/1/")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    pytest.main([__file__])
