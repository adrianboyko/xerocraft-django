from django import forms
from django.forms.widgets import TextInput
from django.core.validators import ValidationError
from django.contrib.auth import authenticate
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML, Div
from datetime import datetime, date


class NumberInput(TextInput):
    input_type = 'number'


def is_today_or_earlier_date_validator(value):
    if value > date.today():
        raise ValidationError("{0} is a future date.".format(value))

