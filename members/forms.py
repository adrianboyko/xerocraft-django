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


# REVIEW: Use ModelForm instead?
class Books_NotePaymentForm(forms.Form):

    userid      = forms.CharField(max_length=64, label="Userid:")
    password    = forms.CharField(max_length=20, label="Password:", widget=forms.PasswordInput())
    amt_paid    = forms.DecimalField(max_digits=5, decimal_places=2, label="Amount Paid by Member:")
    when_paid   = forms.DateTimeField(label="Date/Time on which Member Paid:")
    service     = forms.CharField(max_length=20, label="Service that Processed the Payment:")
    service_fee = forms.DecimalField(max_digits=5, decimal_places=2, label="Service Fee:")
    service_id  = forms.CharField(max_length=20, label="Service's ID for Payment:")
    duration    = forms.CharField(max_length=5, label="Duration of Paid Membership:")
    fname       = forms.CharField(max_length=30, label="First Name of Member:")
    lname       = forms.CharField(max_length=30, label="Last Name of Member:")
    email       = forms.EmailField(label="Email Address of Member:")
    family      = forms.IntegerField(label="Additonal Family Members:")

