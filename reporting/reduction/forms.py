"""
    Forms for auto-reduction configuration
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
from django import forms
from django.core.exceptions import ValidationError
from models import ReductionProperty, PropertyModification
import sys
import re
import logging
import view_util

class ReductionConfigurationSEQForm(forms.Form):
    """
        Configuration form for SEQ reduction
    """
    use_default = forms.BooleanField(required=False, initial=False)
    mask = forms.CharField(required=False, initial='')
    raw_vanadium = forms.CharField(required=False, initial='')
    processed_vanadium = forms.CharField(required=False, initial='')
    grouping = forms.CharField(required=False, initial='')
    e_min = forms.FloatField(required=True, initial=-0.2)
    e_step = forms.FloatField(required=True, initial=0.015)
    e_max = forms.FloatField(required=True, initial=0.95)
    
    ## List of field that are used in the template
    _template_list = ['mask', 'raw_vanadium', 'processed_vanadium', 'grouping',
                      'e_min', 'e_step', 'e_max', 'use_default']
    
    def to_db(self, instrument_id, user=None):
        """
            Store the form data
            
            @param instrument_id: Instrument object
            @param user: user that made the change
        """
        for key in self._template_list:
            try:
                if key in self.cleaned_data:
                    value = str(self.cleaned_data[key])
                else:
                    value = ''
                view_util.store_property(instrument_id, key, value, user=user)
            except:
                logging.error("ReductionConfigurationSEQForm.to_db: %s" % sys.exc_value)

    def to_template(self):
        template_dict = {}
        for key in self._template_list:
            if key in self.cleaned_data:
                template_dict[key] = str(self.cleaned_data[key])
            else:
                template_dict[key] = ''
        return template_dict

def validate_integer_list(value):
    """
        Allow for "1,2,3" and "1-3"
        
        @param value: string value to parse
    """
    # Look for a list of ranges
    range_list = value.split(',')
    for range in range_list:
        for item in range.split('-'):
            try:
                int(item.strip())
            except:
                raise ValidationError(u'Error parsing %s for a range of integers' % value)

class MaskForm(forms.Form):
    """
        Simple form for a mask entry.
        A combination of banks, tubes, pixels can be specified.
    """
    bank = forms.CharField(required=False, initial='', validators=[validate_integer_list])
    tube = forms.CharField(required=False, initial='', validators=[validate_integer_list])
    pixel = forms.CharField(required=False, initial='', validators=[validate_integer_list])
    remove = forms.BooleanField(required=False, initial=False)
    
    @classmethod
    def to_tokens(cls, value):
        """
            Takes a block of Mantid script and extract the
            dictionary argument. The template should be like
            
            MaskBTPParameters({'Bank':'', 'Tube':'', 'Pixel':''})
            
            @param value: string value for the code snippet
        """
        mask_list = []
        try:
            lines = value.split('\n')
            for line in lines:
                if 'MaskBTPParameters' in line:
                    mask_strings = re.findall("append\((.+)\)", line.strip())
                    for item in mask_strings:
                        mask_list.append( eval(item.lower()) )
        except:
            logging.error("MaskForm count not parse a command line: %s" % sys.exc_value)
        return mask_list
    
    @classmethod
    def to_python(cls, mask_list, indent='    '):
        """
            Take a block of Mantid script from a list of mask forms
            
            @param mask_list: list of MaskForm objects
            @param indent: string indentation to add to each line
        """
        command_list = ''
        for mask in mask_list:
            if 'remove' in mask.cleaned_data and mask.cleaned_data['remove'] == True:
                continue
            command_str = str(mask)
            if len(command_str)>0:
                command_list += "%s%s\n" % (indent, command_str)
        return command_list

    def __str__(self):
        """
            Return a string representing the Mantid command to run
            for this mask item.
        """
        entry_dict = {}
        if 'bank' in self.cleaned_data and len(self.cleaned_data['bank'].strip())>0:
            entry_dict["Bank"] = str(self.cleaned_data['bank'])
        if 'tube' in self.cleaned_data and len(self.cleaned_data['tube'].strip())>0:
            entry_dict["Tube"] = str(self.cleaned_data['tube'])
        if 'pixel' in self.cleaned_data and len(self.cleaned_data['pixel'].strip())>0:
            entry_dict["Pixel"] = str(self.cleaned_data['pixel'])
        if len(entry_dict)==0:
            return ""
        return "MaskBTPParameters.append(%s)" % str(entry_dict)
    
