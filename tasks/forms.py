from django import forms
from django.forms.widgets import TextInput
from django.core.validators import MaxValueValidator
from django.contrib.auth import authenticate
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML, Div
from datetime import datetime


class NumberInput(TextInput):
    input_type = 'number'


class Desktop_TimeSheetForm(forms.Form):

    id_verify = forms.BooleanField(label="[SET IN __INIT__]")

    work_desc = forms.CharField(max_length=512, label="Description of work done: ",
        widget=forms.Textarea(attrs={'placeholder':'E.g. Staffed front desk during open hack.'}))

    work_date = forms.DateField(
        widget=forms.TextInput(attrs={'class': 'datepicker', 'placeholder':'MM/DD/YYYY'}),
        label="Date on which work was done: ",
        validators=[MaxValueValidator(datetime.today().date())], # Don't allow future dates
    )

    work_time = forms.TimeField(
        input_formats=['%I:%M %p'],
        widget=forms.TimeInput(format='%I:%M %p', attrs={'class': 'timepicker', 'placeholder':'HH:MM AM'}),
        label="Time at which work was begun: "
    )

    work_dur = forms.DecimalField(widget=NumberInput(attrs={'min':0, 'step':0.25, 'class':'durpicker', 'placeholder':'#.## (e.g. 5.25)'}),
        label="Hours of work done: ")

    witness_id = forms.CharField(label="Witness U or E: ",max_length=50)

    witness_pw = forms.CharField(label="Witness Password: ", widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('request', None).user
        id = ""
        if user.first_name is not None: id += user.first_name
        if user.last_name is not None: id += " " + user.last_name
        if id == "": id = user.username
        self.base_fields['id_verify'].label = "I am %s %s." % (user.first_name, user.last_name)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'id_verify',
            'work_desc',
            'work_date',
            'work_time',
            'work_dur',
            'witness_id',
            'witness_pw',
            Submit('submit', 'Submit', css_class='button white'),
        )
        super(Desktop_TimeSheetForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(Desktop_TimeSheetForm, self).clean()
        witness_id = cleaned_data.get('witness_id')
        witness_pw = cleaned_data.get('witness_pw')
        if not authenticate(username=witness_id, password=witness_pw):
            self.add_error('witness_id',"Witness id or pw is incorrect.")

