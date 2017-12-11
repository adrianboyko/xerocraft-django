

# Standard
from datetime import timedelta

# Third Party
from django.core.exceptions import ValidationError

# Local


def positive_duration(value: timedelta):
    message = 'Duration must be greater than zero.'
    if value <= timedelta(0):
        raise ValidationError(message, params={'value': value})