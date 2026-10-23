from django.conf import settings
from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse

from reporting.reduction.models import Choice, ReductionProperty
from reporting.report.models import Instrument


class TestView(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="user1", password="pw").save()

        Instrument.objects.create(name="inst").save()
        Instrument.objects.create(name="corelli").save()
        Instrument.objects.create(name="ref_m").save()

        instrument = Instrument(name="cncs")
        instrument.save()

        grp_prop = ReductionProperty(instrument=instrument, key="grouping")
        grp_prop.save()

        Choice(instrument=instrument, property=grp_prop, value="grp1", description="group1").save()

        instrument = Instrument(name="seq")
        instrument.save()

        grp_prop = ReductionProperty(instrument=instrument, key="grouping")
        grp_prop.save()

        Choice(instrument=instrument, property=grp_prop, value="grp1", description="group1").save()

        instrument = Instrument(name="arcs")
        instrument.save()

        grp_prop = ReductionProperty(instrument=instrument, key="grouping")
        grp_prop.save()

        Choice(instrument=instrument, property=grp_prop, value="grp1", description="group1").save()

    @classmethod
    def classTearDown(cls):
        Instrument.objects.all().delete()
        User.objects.all().delete()
        ReductionProperty.objects.all().delete()

    def setUp(self):
        self.assertTrue(self.client.login(username="user1", password="pw"))

    def test_arcs(self):
        # GET
        response = self.client.get(reverse("reduction:configuration", args=["arcs"]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reduction/configuration_dgs.html")

        # POST
        response = self.client.post(
            reverse("reduction:configuration", args=["arcs"]),
            data={
                "button_choice": "submit",
                "e_min": -0.2,
                "e_step": 0.015,
                "e_max": 0.95,
                "grouping": "grp1",
                "form-INITIAL_FORMS": "0",
                "form-TOTAL_FORMS": "0",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reduction/configuration_dgs.html")

    def test_seq(self):
        # GET
        response = self.client.get(reverse("reduction:configuration", args=["seq"]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reduction/configuration_seq.html")

        # POST
        response = self.client.post(
            reverse("reduction:configuration", args=["seq"]),
            data={
                "button_choice": "submit",
                "e_min": -0.2,
                "e_step": 0.015,
                "e_max": 0.95,
                "grouping": "grp1",
                "create_elastic_nxspe": True,
                "form-INITIAL_FORMS": "0",
                "form-TOTAL_FORMS": "0",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reduction/configuration_seq.html")

    def test_corelli(self):
        response = self.client.get(reverse("reduction:configuration", args=["corelli"]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reduction/configuration_corelli.html")

        # POST
        response = self.client.post(
            reverse("reduction:configuration", args=["corelli"]),
            data={
                "button_choice": "submit",
                "form-INITIAL_FORMS": "0",
                "form-TOTAL_FORMS": "0",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reduction/configuration_corelli.html")

    def test_cncs(self):
        # GET
        response = self.client.get(reverse("reduction:configuration", args=["cncs"]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reduction/configuration_cncs.html")

        # POST
        response = self.client.post(
            reverse("reduction:configuration", args=["cncs"]),
            data={
                "button_choice": "submit",
                "form-INITIAL_FORMS": "0",
                "form-TOTAL_FORMS": "0",
                "vanadium_integration_min": "13",
                "vanadium_integration_max": "42",
                "e_min": "-1",
                "e_step": "1",
                "e_max": "10",
                "a": "1",
                "b": "2",
                "c": "3",
                "alpha": "10",
                "beta": "20",
                "gamma": "30",
                "grouping": "grp1",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reduction/configuration_cncs.html")

    def test_ref_m(self):
        # GET
        response = self.client.get(reverse("reduction:configuration", args=["ref_m"]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reduction/configuration_ref_m.html")

        # POST
        response = self.client.post(
            reverse("reduction:configuration", args=["ref_m"]),
            data={
                "button_choice": "submit",
                # Options for all samples in the run
                "use_const_q": False,
                "q_step": -0.02,
                "use_sangle": True,
                "fit_peak_in_roi": False,
                "peak_count": 3,
                # Options for first sample
                "force_peak": False,
                "peak_min": 160,
                "peak_max": 170,
                "use_roi_bck": False,
                "force_background": False,
                "bck_min": 5,
                "bck_max": 100,
                "use_side_bck": False,
                "bck_width": 10,
                "force_low_res": False,
                "low_res_min": 42,
                "low_res_max": 142,
                # Options for second peak
                "force_peak_s2": True,
                "peak_min_s2": 170,
                "peak_max_s2": 180,
                "use_roi_bck_s2": True,
                "force_background_s2": True,
                "bck_min_s2": 6,
                "bck_max_s2": 101,
                "use_side_bck_s2": True,
                "bck_width_s2": 11,
                "force_low_res_s2": True,
                "low_res_min_s2": 91,
                "low_res_max_s2": 181,
                # Options for third peak
                "force_peak_s3": False,
                "peak_min_s3": 180,
                "peak_max_s3": 190,
                "use_roi_bck_s3": False,
                "force_background_s3": False,
                "bck_min_s3": 7,
                "bck_max_s3": 102,
                "use_side_bck_s3": False,
                "bck_width_s3": 12,
                "force_low_res_s3": False,
                "low_res_min_s3": 66,
                "low_res_max_s3": 166,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reduction/configuration_ref_m.html")
        # uncomment the following line only when debugging, in order to inspect the response content
        # open("/tmp/junk.html", "wb").write(response.content)  # take a look to file:///tmp/junk.html with the browser

    def test_configuration_change(self):
        # no data
        response = self.client.post(reverse("reduction:configuration_change", args=["inst"]))

        # should succeed with connection closed
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Connection"], "close")

        # with data
        response = self.client.post(
            reverse("reduction:configuration_change", args=["inst"]),
            data={"data": '{"value":"value"}', "use_default": True},
        )

        # should fail to send ActiveMQ request
        self.assertEqual(response.status_code, 500)

    def test_configuration_update(self):
        response = self.client.post(reverse("reduction:configuration_update", args=["inst"]))
        # should succeed with connection closed
        self.assertEqual(response.status_code, 200)

    def test_configuration_change_checks_csrf(self):
        client = Client(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="user1", password="pw"))
        response = client.post(reverse("reduction:configuration_change", args=["inst"]))
        self.assertEqual(response.status_code, 403)


class TestInstrumentTeamRequired(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(username="outsider", password="pw")
        member = User.objects.create_user(username="member", password="pw")
        team = Group.objects.create(name=f"ARCS{settings.INSTRUMENT_TEAM_SUFFIX}")
        member.groups.add(team)

        instrument = Instrument.objects.create(name="arcs")
        grp_prop = ReductionProperty.objects.create(instrument=instrument, key="grouping")
        Choice.objects.create(instrument=instrument, property=grp_prop, value="grp1", description="group1")

    def test_outsider_can_look_but_not_change(self):
        self.assertTrue(self.client.login(username="outsider", password="pw"))
        url = reverse("reduction:configuration", args=["arcs"])
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, data={"button_choice": "reset"})
        self.assertEqual(response.status_code, 403)
        self.assertIn(b"Only the ARCS instrument team", response.content)

        change = {"data": '[{"key": "grouping", "value": "x"}]'}
        response = self.client.post(reverse("reduction:configuration_change", args=["arcs"]), data=change)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(ReductionProperty.objects.get(key="grouping").value, "")

    def test_team_member_can_change(self):
        self.assertTrue(self.client.login(username="member", password="pw"))
        response = self.client.post(reverse("reduction:configuration", args=["arcs"]), data={"button_choice": "reset"})
        self.assertEqual(response.status_code, 302)

    def test_webmon_admin_can_change(self):
        # admins aren't on the team but can already edit these settings in the Django admin
        User.objects.create_user(username="admin", password="pw", is_staff=True)
        self.assertTrue(self.client.login(username="admin", password="pw"))
        response = self.client.post(reverse("reduction:configuration", args=["arcs"]), data={"button_choice": "reset"})
        self.assertEqual(response.status_code, 302)
