from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from report.models import Instrument
from reduction.models import ReductionProperty, Choice


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

    def test_inst(self):
        response = self.client.get(reverse("reduction:configuration", args=["inst"]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reduction/configuration.html")

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
                "bck_width": 10,
                "peak_min": 160,
                "peak_max": 170,
                "bck_min": 5,
                "bck_max": 100,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reduction/configuration_ref_m.html")

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
