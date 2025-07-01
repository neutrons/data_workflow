from django.test import TestCase

from reporting.reduction import forms
from reporting.reduction.models import Choice, ReductionProperty
from reporting.report.models import Instrument


class TestREF_MForm(TestCase):
    default_test_fields = {
        "skip_quicknxs": False,
        # Options for all peaks in the run
        "use_const_q": False,
        "q_step": -0.02,
        "use_sangle": True,
        "fit_peak_in_roi": False,
        "peak_count": 1,
        # Options for first peak
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
        "force_peak_s2": False,
        "peak_min_s2": 160,
        "peak_max_s2": 170,
        "use_roi_bck_s2": False,
        "force_background_s2": False,
        "bck_min_s2": 5,
        "bck_max_s2": 100,
        "use_side_bck_s2": False,
        "bck_width_s2": 10,
        "force_low_res_s2": False,
        "low_res_min_s2": 42,
        "low_res_max_s2": 142,
        # Options for third peak
        "force_peak_s3": False,
        "peak_min_s3": 160,
        "peak_max_s3": 170,
        "use_roi_bck_s3": False,
        "force_background_s3": False,
        "bck_min_s3": 5,
        "bck_max_s3": 100,
        "use_side_bck_s3": False,
        "bck_width_s3": 10,
        "force_low_res_s3": False,
        "low_res_min_s3": 42,
        "low_res_max_s3": 142,
    }

    def test_empty_form(self):
        form = forms.ReductionConfigurationREF_MForm({})
        self.assertFalse(form.is_valid())  # empty instantiated form invalid because fields like `peak_min` are required
        self.assertEqual(len(form.to_template()), len(self.default_test_fields) - 1)  # `skip_quicknxs` missing
        for key in self.default_test_fields:
            self.assertTrue(key in form.fields)
        # check the values for an empty form. Field values do not correspond to initial values
        self.assertEqual(
            form.to_template(),
            {
                # Options for all peaks in the run
                "use_const_q": "False",
                "q_step": "None",
                "use_sangle": "False",
                "fit_peak_in_roi": "False",
                "peak_count": "",
                # Options for first peak
                "force_peak": "False",
                "peak_min": "",
                "peak_max": "",
                "use_roi_bck": "False",
                "force_background": "False",
                "bck_min": "",
                "bck_max": "",
                "use_side_bck": "False",
                "bck_width": "",
                "force_low_res": "False",
                "low_res_min": "",
                "low_res_max": "",
                # Options for second peak
                "force_peak_s2": "False",
                "peak_min_s2": "",
                "peak_max_s2": "",
                "use_roi_bck_s2": "False",
                "force_background_s2": "False",
                "bck_min_s2": "",
                "bck_max_s2": "",
                "use_side_bck_s2": "False",
                "bck_width_s2": "",
                "force_low_res_s2": "False",
                "low_res_min_s2": "",
                "low_res_max_s2": "",
                # Options for third peak
                "force_peak_s3": "False",
                "peak_min_s3": "",
                "peak_max_s3": "",
                "use_roi_bck_s3": "False",
                "force_background_s3": "False",
                "bck_min_s3": "",
                "bck_max_s3": "",
                "use_side_bck_s3": "False",
                "bck_width_s3": "",
                "force_low_res_s3": "False",
                "low_res_min_s3": "",
                "low_res_max_s3": "",
            },
        )

    def test_form_filled(self):
        form = forms.ReductionConfigurationREF_MForm(self.default_test_fields)
        form.full_clean()  # Clean all of form.data and populate form._errors and form.cleaned_data.
        for key, val in self.default_test_fields.items():
            self.assertEqual(form.cleaned_data.get(key), val)
        self.assertTrue(form.is_valid())
        # form.to_template() returns a dictionary where fields values have been cast as a string
        self.assertEqual(
            {**form.to_template(), **{"skip_quicknxs": "False"}},
            {k: str(v) for k, v in self.default_test_fields.items()},
        )

        # this should do nothing, but shouldn't fail
        form.set_instrument("nonexist")

    def test_to_db(self):
        test_fields = {"bck_width_s3": 11}
        form = forms.ReductionConfigurationREF_MForm(test_fields)
        self.assertFalse(form.is_valid())  # invalid because fields like `peak_min` are required

        instrument = Instrument(name="inst")
        instrument.save()

        form.to_db(instrument)

        # check some things get set
        use_sangle = ReductionProperty.objects.filter(instrument=instrument, key="use_sangle")
        self.assertEqual(len(use_sangle), 1)
        self.assertEqual(use_sangle[0].value, "")

        bck_width_s3 = ReductionProperty.objects.filter(instrument=instrument, key="bck_width_s3")
        self.assertEqual(len(bck_width_s3), 1)
        self.assertEqual(bck_width_s3[0].value, "11")

    def test_to_db_bad(self):
        # no clean data
        form = forms.ReductionConfigurationREF_MForm({})
        form.to_db(0)
        self.assertEqual(len(ReductionProperty.objects.filter()), 0)


class TestCNCSForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        instrument = Instrument(name="inst")
        instrument.save()

        grp_prop = ReductionProperty(instrument=instrument, key="grouping")
        grp_prop.save()

        Choice(instrument=instrument, property=grp_prop, value="grp1", description="group1").save()

    @classmethod
    def testTearDown(cls):
        Instrument.objects.all().delete()
        ReductionProperty.objects.all().delete()

    def test_form_filled_just_required(self):
        test_fields = {
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
        }

        form = forms.ReductionConfigurationCNCSForm(test_fields)
        form.set_instrument("inst")

        self.assertTrue(form.is_valid())

    def test_valid_float_list(self):
        test_fields = {
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
            "t0": "1.2,6.7",
        }

        form = forms.ReductionConfigurationCNCSForm(test_fields)
        form.set_instrument("inst")

        self.assertTrue(form.is_valid())

    def test_invalid_float_list(self):
        test_fields = {
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
            "t0": "1.2,6.7,a",
        }

        form = forms.ReductionConfigurationCNCSForm(test_fields)
        form.set_instrument("inst")

        self.assertFalse(form.is_valid())


class TestDGSForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        instrument = Instrument(name="dgs")
        instrument.save()

        grp_prop = ReductionProperty(instrument=instrument, key="grouping")
        grp_prop.save()

        Choice(instrument=instrument, property=grp_prop, value="grp1", description="group1").save()

    @classmethod
    def testTearDown(cls):
        Instrument.objects.all().delete()
        ReductionProperty.objects.all().delete()

    def test_form_filled_just_required(self):
        test_fields = {"e_min": -1.0, "e_step": 0.1, "e_max": 1.0, "grouping": "grp1"}

        form = forms.ReductionConfigurationDGSForm(test_fields)
        form.set_instrument("dgs")

        self.assertTrue(form.is_valid())

    def test_not_setting_instrument(self):
        test_fields = {"e_min": -1.0, "e_step": 0.1, "e_max": 1.0, "grouping": "grp1"}

        form = forms.ReductionConfigurationDGSForm(test_fields)

        self.assertFalse(form.is_valid())

    def test_set_invalid_instrument(self):
        test_fields = {"e_min": -1.0, "e_step": 0.1, "e_max": 1.0, "grouping": "grp1"}

        form = forms.ReductionConfigurationDGSForm(test_fields)
        form.set_instrument("nonexistent")

        self.assertFalse(form.is_valid())


class TestSEQForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        instrument = Instrument(name="seq")
        instrument.save()

        grp_prop = ReductionProperty(instrument=instrument, key="grouping")
        grp_prop.save()

        Choice(instrument=instrument, property=grp_prop, value="grp1", description="group1").save()

    @classmethod
    def testTearDown(cls):
        Instrument.objects.all().delete()
        ReductionProperty.objects.all().delete()

    def test_form_filled(self):
        test_fields = {
            "e_min": -1.0,
            "e_step": 0.1,
            "e_max": 1.0,
            "grouping": "grp1",
            "create_elastic_nxspe": True,
        }

        form = forms.ReductionConfigurationSEQForm(test_fields)
        form.set_instrument("seq")

        self.assertTrue(form.is_valid())


class TestCorelliForm(TestCase):
    def test_form_filled_default(self):
        form = forms.ReductionConfigurationCorelliForm({})

        self.assertTrue(form.is_valid())

        self.assertEqual(
            form.to_template(),
            {
                "mask": "",
                "plot_requests": "",
                "ub_matrix_file": "",
                "useCC": "False",
                "vanadium_SA_file": "",
                "vanadium_flux_file": "",
            },
        )


class TestMaskForm(TestCase):
    def test_from_filled_empty(self):
        form = forms.MaskForm({})
        self.assertTrue(form.is_valid())

        self.assertEqual(str(form), "")

    def test_from_filled(self):
        form = forms.MaskForm({"pixel": "1-8,121-128", "tube": "2", "bank": "3-5"})
        self.assertTrue(form.is_valid())

        self.assertEqual(
            str(form),
            "MaskBTPParameters.append({'Bank': '3-5', 'Tube': '2', 'Pixel': '1-8,121-128'})",
        )

    def test_invalid_integer_list(self):
        form = forms.MaskForm({"pixel": "1-8,121-128,h"})
        self.assertFalse(form.is_valid())

    def test_to_tokens(self):
        script = """MaskBTPParameters.append({'Pixel': '1-8,121-128'})
MaskBTPParameters.append({'Bank': '3-5'})
MaskBTPParameters.append({'Tube': '2'})"""
        self.assertEqual(
            forms.MaskForm.to_tokens(script),
            [{"pixel": "1-8,121-128"}, {"bank": "3-5"}, {"tube": "2"}],
        )

    def test_to_tokens_bad(self):
        script = """MaskBTPParameters.append({'Pixel': '1-8,121-128'})
MaskBTPParameters.append({'Bank': bad})
MaskBTPParameters.append({'Tube': '2'})"""
        self.assertEqual(forms.MaskForm.to_tokens(script), [{"pixel": "1-8,121-128"}])

    def test_to_python(self):
        mask_list = [
            forms.MaskForm({"pixel": "1-8,121-128"}),
            forms.MaskForm({"tube": "2", "remove": True}),
            forms.MaskForm({"bank": "3-5"}),
        ]
        for m in mask_list:
            self.assertTrue(m.is_valid())
        self.assertEqual(
            forms.MaskForm.to_python(mask_list, indent=""),
            """MaskBTPParameters.append({'Pixel': '1-8,121-128'})
MaskBTPParameters.append({'Bank': '3-5'})
""",
        )

    def test_to_dict_list(self):
        mask_list = [
            forms.MaskForm({"pixel": "1-8,121-128"}),
            forms.MaskForm({"tube": "2"}),
            forms.MaskForm({"bank": "3-5"}),
        ]
        for mask in mask_list:
            self.assertTrue(mask.is_valid())
        self.assertEqual(
            forms.MaskForm.to_dict_list(mask_list),
            [{"Pixel": "1-8,121-128"}, {"Tube": "2"}, {"Bank": "3-5"}],
        )

    def test_from_dict_list(self):
        dict_list = "[{'Pixel':'1-8,121-128'},{'Bank':'3-5'},{'Tube':'2'}]"
        self.assertEqual(
            forms.MaskForm.from_dict_list(dict_list),
            [{"pixel": "1-8,121-128"}, {"bank": "3-5"}, {"tube": "2"}],
        )


class TestPlottingForm(TestCase):
    def test_to_dict_list(self):
        plot_list = [
            forms.PlottingForm({"maximum": 0.05, "minimum": -0.05, "perpendicular_to": "[0,K,0]"}),
            forms.PlottingForm({"maximum": 1.05, "minimum": 0.95, "perpendicular_to": "[H,0,0]"}),
        ]
        for plot in plot_list:
            self.assertTrue(plot.is_valid())
        self.assertEqual(
            forms.PlottingForm.to_dict_list(plot_list),
            [
                {"PerpendicularTo": "[0,K,0]", "Minimum": "-0.05", "Maximum": "0.05"},
                {"PerpendicularTo": "[H,0,0]", "Maximum": "1.05", "Minimum": "0.95"},
            ],
        )

    def test_from_dict_list(self):
        dict_list = (
            "[{'PerpendicularTo':'[0,K,0]','Minimum':'not-a-number','Maximum':'not-a-number'},"
            "{'PerpendicularTo':'[H,0,0]','Minimum':'0.95','Maximum':'1.05'}]"
        )
        self.assertEqual(
            forms.PlottingForm.from_dict_list(dict_list),
            [
                {"maximum": 0.05, "minimum": -0.05, "perpendicular_to": "[0,K,0]"},
                {"maximum": 1.05, "minimum": 0.95, "perpendicular_to": "[H,0,0]"},
            ],
        )

        dict_list = "{'PerpendicularTo':'[0,0,L]','Minimum':'7','Maximum':'12'}"
        self.assertEqual(
            forms.PlottingForm.from_dict_list(dict_list),
            [{"maximum": 12.0, "minimum": 7.0, "perpendicular_to": "[0,0,L]"}],
        )
