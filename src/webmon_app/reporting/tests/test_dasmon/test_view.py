import pytest
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from workflow.database.report.models import IPTS, DataRun, WorkflowSummary

from reporting.dasmon.models import ActiveInstrument, Instrument, Signal


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
        refstr_1 = "'first_run_id': 1"
        refstr_2 = "'last_run_id': 4"
        self.assertTrue(refstr_1 in str(response.context))
        self.assertTrue(refstr_2 in str(response.context))


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


class LegacyMonitorViewTest(TestCase):
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
        response = self.client.get("/dasmon/test_instrument/legacy/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("dasmon:legacy_monitor", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("dasmon:legacy_monitor", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dasmon/legacy_monitor.html")

    def test_list_instrument(self):
        response = self.client.get(reverse("dasmon:legacy_monitor", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)
        assert "test_instrument" in str(response.context)


class LegacyMonitorUpdateViewTest(TestCase):
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
        response = self.client.get("/dasmon/test_instrument/legacy/update/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("dasmon:get_legacy_data", args=["test_instrument"]))
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
        # NOTE:
        # The id will not start from 1 as Django will use larger
        # int for new record even if the old record is purged, the only thing
        # we can check is to make sure that the context has those entries.
        refstr_1 = "first_run_id"
        refstr_2 = "last_run_id"
        self.assertTrue(refstr_1 in str(response.context))
        self.assertTrue(refstr_2 in str(response.context))


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


class GetSignalTableViewTest(TestCase):
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
            #
            Signal(
                instrument_id=inst,
                name=f"sig_{rn}",
                source=f"src_{rn}",
                message=f"msg_{rn}",
                level=rn,
                timestamp=timezone.now(),
            ).save()

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="ipts_test").delete()
        DataRun.objects.all().delete()
        WorkflowSummary.objects.all().delete()
        Signal.objects.all().delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/dasmon/test_instrument/signals/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse("dasmon:get_signal_table", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)

    def test_list_signals(self):
        response = self.client.get(reverse("dasmon:get_signal_table", args=["test_instrument"]))
        self.assertEqual(response.status_code, 200)
        for d in response.context:
            if "signals" in d:
                self.assertEqual(len(d["signals"]), 4)


class AcknowledgeSignalViewTest(TestCase):
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
            #
            Signal(
                instrument_id=inst,
                name=f"sig_{rn}",
                source=f"src_{rn}",
                message=f"msg_{rn}",
                level=rn,
                timestamp=timezone.now(),
            ).save()

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="ipts_test").delete()
        DataRun.objects.all().delete()
        WorkflowSummary.objects.all().delete()
        Signal.objects.all().delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/dasmon/test_instrument/signals/ack/1/")
        self.assertEqual(response.status_code, 200)

    def test_view_exists_by_name(self):
        response = self.client.get(reverse("dasmon:acknowledge_signal", args=["test_instrument", 1]))
        self.assertEqual(response.status_code, 200)


class NotificationsViewTest(TestCase):
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
            #
            Signal(
                instrument_id=inst,
                name=f"sig_{rn}",
                source=f"src_{rn}",
                message=f"msg_{rn}",
                level=rn,
                timestamp=timezone.now(),
            ).save()

    @classmethod
    def tearDownClass(cls):
        User.objects.get(username="testuser").delete()
        Instrument.objects.get(name="test_instrument").delete()
        IPTS.objects.get(expt_name="ipts_test").delete()
        DataRun.objects.all().delete()
        WorkflowSummary.objects.all().delete()
        Signal.objects.all().delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="testuser", password="12345"))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/dasmon/notifications/")
        self.assertEqual(response.status_code, 200)

    def test_view_exists_by_name(self):
        response = self.client.get(reverse("dasmon:notifications"))
        self.assertEqual(response.status_code, 200)

    def test_list_notifications(self):
        response = self.client.get(reverse("dasmon:notifications"))
        self.assertEqual(response.status_code, 200)
        assert len(response.context) == (1 + 1 + 4 * 2)


if __name__ == "__main__":
    pytest.main([__file__])
