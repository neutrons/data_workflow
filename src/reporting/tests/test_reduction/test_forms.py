from django.test import TestCase
from reduction import forms
from report.models import Instrument
from reduction.models import ReductionProperty, Choice


class TestREFMForm(TestCase):
    def test_empty_form(self):
        default_test_fields = {
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

        form = forms.ReductionConfigurationREFMForm({})
        self.assertFalse(form.is_valid())
        for key in default_test_fields:
            self.assertTrue(key in form.fields)

        self.assertEqual(form.to_template(), {'bck_max': '',
                                              'bck_min': '',
                                              'bck_width': '',
                                              'const_q_cutoff': 'None',
                                              'fit_peak_in_roi': 'False',
                                              'force_background': 'False',
                                              'force_peak': 'False',
                                              'peak_max': '',
                                              'peak_min': '',
                                              'plot_in_2D': 'False',
                                              'q_step': 'None',
                                              'skip_quicknxs': 'False',
                                              'use_const_q': 'False',
                                              'use_roi_bck': 'False',
                                              'use_sangle': 'False',
                                              'use_side_bck': 'False'})

    def test_form_filled(self):
        test_fields = {
            'use_sangle': False,
            'use_const_q': True,
            'use_roi_bck': True,
            'const_q_cutoff': 0.04,
            'use_side_bck': True,
            'bck_width': 11,
            'fit_peak_in_roi': True,
            'force_peak': True,
            'plot_in_2D': True,
            'peak_min': 170,
            'peak_max': 160,
            'force_background': True,
            'bck_min': 6,
            'bck_max': 1000,
            'skip_quicknxs': True,
            'q_step': -0.03,
        }

        form = forms.ReductionConfigurationREFMForm(test_fields)
        form.full_clean()
        for key, val in test_fields.items():
            self.assertEqual(form.cleaned_data.get(key), val)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.to_template(),
                         {'use_sangle': 'False',
                          'use_const_q': 'True',
                          'const_q_cutoff': '0.04',
                          'fit_peak_in_roi': 'True',
                          'plot_in_2D': 'True',
                          'force_peak': 'True',
                          'peak_min': '170',
                          'peak_max': '160',
                          'q_step': '-0.03',
                          'force_background': 'True',
                          'bck_min': '6',
                          'bck_max': '1000',
                          'use_roi_bck': 'True',
                          'use_side_bck': 'True',
                          'bck_width': '11',
                          'skip_quicknxs': 'True'})

        # this should do nothing, but shouldn't fail
        form.set_instrument('nonexist')

    def test_to_db(self):
        test_fields = {'const_q_cutoff': 0.04,
                       'bck_width': 11}
        form = forms.ReductionConfigurationREFMForm(test_fields)
        self.assertFalse(form.is_valid())

        instrument = Instrument(name='inst')
        instrument.save()

        form.to_db(instrument)

        # check some things get set
        use_sangle = ReductionProperty.objects.filter(instrument=instrument, key='use_sangle')
        self.assertEqual(len(use_sangle), 1)
        self.assertEqual(use_sangle[0].value, '')

        const_q_cutoff = ReductionProperty.objects.filter(instrument=instrument, key='const_q_cutoff')
        self.assertEqual(len(const_q_cutoff), 1)
        self.assertEqual(const_q_cutoff[0].value, '0.04')

        bck_width = ReductionProperty.objects.filter(instrument=instrument, key='bck_width')
        self.assertEqual(len(bck_width), 1)
        self.assertEqual(bck_width[0].value, '11')

    def test_to_db_bad(self):
        # no clean data
        form = forms.ReductionConfigurationREFMForm({})
        form.to_db(0)
        self.assertEqual(len(ReductionProperty.objects.filter()), 0)


class TestCNCSForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        instrument = Instrument(name='inst')
        instrument.save()

        grp_prop = ReductionProperty(instrument=instrument, key='grouping')
        grp_prop.save()

        Choice(instrument=instrument, property=grp_prop, value='grp1', description='group1').save()

    @classmethod
    def testTearDown(cls):
        Instrument.objects.all().delete()
        ReductionProperty.objects.all().delete()

    def test_form_filled_just_required(self):
        test_fields = {'vanadium_integration_min': '13',
                       'vanadium_integration_max': '42',
                       'e_min': '-1',
                       'e_step': '1',
                       'e_max': '10',
                       'a': '1',
                       'b': '2',
                       'c': '3',
                       'alpha': '10',
                       'beta': '20',
                       'gamma': '30',
                       'grouping': 'grp1'}

        form = forms.ReductionConfigurationCNCSForm(test_fields)
        form.set_instrument('inst')

        self.assertTrue(form.is_valid())

    def test_valid_float_list(self):
        test_fields = {'vanadium_integration_min': '13',
                       'vanadium_integration_max': '42',
                       'e_min': '-1',
                       'e_step': '1',
                       'e_max': '10',
                       'a': '1',
                       'b': '2',
                       'c': '3',
                       'alpha': '10',
                       'beta': '20',
                       'gamma': '30',
                       'grouping': 'grp1',
                       't0': '1.2,6.7'}

        form = forms.ReductionConfigurationCNCSForm(test_fields)
        form.set_instrument('inst')

        self.assertTrue(form.is_valid())

    def test_invalid_float_list(self):
        test_fields = {'vanadium_integration_min': '13',
                       'vanadium_integration_max': '42',
                       'e_min': '-1',
                       'e_step': '1',
                       'e_max': '10',
                       'a': '1',
                       'b': '2',
                       'c': '3',
                       'alpha': '10',
                       'beta': '20',
                       'gamma': '30',
                       'grouping': 'grp1',
                       't0': '1.2,6.7,a'}

        form = forms.ReductionConfigurationCNCSForm(test_fields)
        form.set_instrument('inst')

        self.assertFalse(form.is_valid())


class TestDGSForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        instrument = Instrument(name='dgs')
        instrument.save()

        grp_prop = ReductionProperty(instrument=instrument, key='grouping')
        grp_prop.save()

        Choice(instrument=instrument, property=grp_prop, value='grp1', description='group1').save()

    @classmethod
    def testTearDown(cls):
        Instrument.objects.all().delete()
        ReductionProperty.objects.all().delete()

    def test_form_filled_just_required(self):
        test_fields = {'e_min': -1.0,
                       'e_step': 0.1,
                       'e_max': 1.0,
                       'grouping': 'grp1'}

        form = forms.ReductionConfigurationDGSForm(test_fields)
        form.set_instrument('dgs')

        self.assertTrue(form.is_valid())

    def test_not_setting_instrument(self):
        test_fields = {'e_min': -1.0,
                       'e_step': 0.1,
                       'e_max': 1.0,
                       'grouping': 'grp1'}

        form = forms.ReductionConfigurationDGSForm(test_fields)

        self.assertFalse(form.is_valid())

    def test_set_invalid_instrument(self):
        test_fields = {'e_min': -1.0,
                       'e_step': 0.1,
                       'e_max': 1.0,
                       'grouping': 'grp1'}

        form = forms.ReductionConfigurationDGSForm(test_fields)
        form.set_instrument('nonexistent')

        self.assertFalse(form.is_valid())


class TestSEQForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        instrument = Instrument(name='seq')
        instrument.save()

        grp_prop = ReductionProperty(instrument=instrument, key='grouping')
        grp_prop.save()

        Choice(instrument=instrument, property=grp_prop, value='grp1', description='group1').save()

    @classmethod
    def testTearDown(cls):
        Instrument.objects.all().delete()
        ReductionProperty.objects.all().delete()

    def test_form_filled(self):
        test_fields = {'e_min': -1.0,
                       'e_step': 0.1,
                       'e_max': 1.0,
                       'grouping': 'grp1',
                       'create_elastic_nxspe': True}

        form = forms.ReductionConfigurationSEQForm(test_fields)
        form.set_instrument('seq')

        self.assertTrue(form.is_valid())


class TestCorelliForm(TestCase):
    def test_form_filled_default(self):
        form = forms.ReductionConfigurationCorelliForm({})

        self.assertTrue(form.is_valid())

        self.assertEqual(form.to_template(), {'mask': '',
                                              'plot_requests': '',
                                              'ub_matrix_file': '',
                                              'useCC': 'False',
                                              'vanadium_SA_file': '',
                                              'vanadium_flux_file': ''})


class TestMaskForm(TestCase):
    def test_from_filled_empty(self):
        form = forms.MaskForm({})
        self.assertTrue(form.is_valid())

        self.assertEqual(str(form), '')

    def test_from_filled(self):
        form = forms.MaskForm({'pixel': '1-8,121-128',
                               'tube': '2',
                               'bank': '3-5'})
        self.assertTrue(form.is_valid())

        self.assertEqual(str(form), "MaskBTPParameters.append({'Bank': '3-5', 'Tube': '2', 'Pixel': '1-8,121-128'})")

    def test_invalid_integer_list(self):
        form = forms.MaskForm({'pixel': '1-8,121-128,h'})
        self.assertFalse(form.is_valid())

    def test_to_tokens(self):
        script = """MaskBTPParameters.append({'Pixel': '1-8,121-128'})
MaskBTPParameters.append({'Bank': '3-5'})
MaskBTPParameters.append({'Tube': '2'})"""
        self.assertEqual(forms.MaskForm.to_tokens(script), [{'pixel': '1-8,121-128'},
                                                            {'bank': '3-5'},
                                                            {'tube': '2'}])

    def test_to_tokens_bad(self):
        script = """MaskBTPParameters.append({'Pixel': '1-8,121-128'})
MaskBTPParameters.append({'Bank': bad})
MaskBTPParameters.append({'Tube': '2'})"""
        self.assertEqual(forms.MaskForm.to_tokens(script), [{'pixel': '1-8,121-128'}])

    def test_to_python(self):
        mask_list = [forms.MaskForm({'pixel': '1-8,121-128'}),
                     forms.MaskForm({'tube': '2', 'remove': True}),
                     forms.MaskForm({'bank': '3-5'})]
        for m in mask_list:
            self.assertTrue(m.is_valid())
        self.assertEqual(forms.MaskForm.to_python(mask_list, indent=''), """MaskBTPParameters.append({'Pixel': '1-8,121-128'})
MaskBTPParameters.append({'Bank': '3-5'})
""")

    def test_to_dict_list(self):
        mask_list = [forms.MaskForm({'pixel': '1-8,121-128'}),
                     forms.MaskForm({'tube': '2'}),
                     forms.MaskForm({'bank': '3-5'})]
        for mask in mask_list:
            self.assertTrue(mask.is_valid())
        self.assertEqual(forms.MaskForm.to_dict_list(mask_list), [{'Pixel': '1-8,121-128'},
                                                                  {'Tube': '2'},
                                                                  {'Bank': '3-5'}])

    def test_from_dict_list(self):
        dict_list = "[{'Pixel':'1-8,121-128'},{'Bank':'3-5'},{'Tube':'2'}]"
        self.assertEqual(forms.MaskForm.from_dict_list(dict_list), [{'pixel': '1-8,121-128'},
                                                                    {'bank': '3-5'},
                                                                    {'tube': '2'}])


class TestPlottingForm(TestCase):
    def test_to_dict_list(self):
        plot_list = [forms.PlottingForm({'maximum': 0.05, 'minimum': -0.05, 'perpendicular_to': '[0,K,0]'}),
                     forms.PlottingForm({'maximum': 1.05, 'minimum': 0.95, 'perpendicular_to': '[H,0,0]'})]
        for plot in plot_list:
            self.assertTrue(plot.is_valid())
        self.assertEqual(forms.PlottingForm.to_dict_list(plot_list),
                         [{'PerpendicularTo': '[0,K,0]', 'Minimum': '-0.05', 'Maximum': '0.05'},
                          {'PerpendicularTo': '[H,0,0]', 'Maximum': '1.05', 'Minimum': '0.95'}])

    def test_from_dict_list(self):
        dict_list = "[{'PerpendicularTo':'[0,K,0]','Minimum':'not-a-number','Maximum':'not-a-number'},"\
            "{'PerpendicularTo':'[H,0,0]','Minimum':'0.95','Maximum':'1.05'}]"
        self.assertEqual(forms.PlottingForm.from_dict_list(dict_list),
                         [{'maximum': 0.05, 'minimum': -0.05, 'perpendicular_to': '[0,K,0]'},
                          {'maximum': 1.05, 'minimum': 0.95, 'perpendicular_to': '[H,0,0]'}])

        dict_list = "{'PerpendicularTo':'[0,0,L]','Minimum':'7','Maximum':'12'}"
        self.assertEqual(forms.PlottingForm.from_dict_list(dict_list),
                         [{'maximum': 12.0, 'minimum': 7.0, 'perpendicular_to': '[0,0,L]'}])
