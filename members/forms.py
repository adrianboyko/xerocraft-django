from django import forms
from django.core.validators import MaxValueValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML, Div
from datetime import datetime


class Desktop_ChooseUserForm(forms.Form):

    # userid can be either username or email. userid is a broader concept than username.
    userid = forms.CharField(max_length=64, label="Enter member's username or email:")

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.layout = Layout(
            'userid',
        )
        super(Desktop_ChooseUserForm, self).__init__(*args, **kwargs)


