from django.test import TestCase
from reduction import forms


class TestREFMForm(TestCase):
    test_fields = {
        'use_sangle': True,
        'use_const_q': False,
        'use_roi_bck': False,
        'const_q_cutoff': 0.02,
        'use_side_bck': False,
        'bck_width': 10,
        'fit_peak_in_roi': False,
        'force_peak': False,
        'plot_in_2D': False,
        'peak_min': 160,
        'peak_max': 170,
        'force_background': False,
        'bck_min': 5,
        'bck_max': 100,
        'skip_quicknxs': False,
        'q_step': -0.02,
    }

    def test_empty_form(self):
        form = forms.ReductionConfigurationREFMForm()
        for key in self.test_fields.keys():
            self.assertTrue(key in form.fields.keys())

    def test_form_filles(self):
        form = forms.ReductionConfigurationREFMForm(self.test_fields)
        form.full_clean()
        for key, val in self.test_fields.items():
            self.assertEqual(form.cleaned_data.get(key), val)
