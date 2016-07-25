
# Standard
import logging
from typing import Sequence

# Third Party
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context

# Local

registrations = {}


class MailView:

    def __init__(self):
        self.logger = logging.getLogger("modelmailer")

    def get_email_spec(self, obj):
        raise NotImplementedError("get_email_spec must be implemented by subclass")

    def send(self, obj):
        try:
            spec = self.get_email_spec(obj)
            params = Context(spec['parameters'])
            text = get_template(spec['template']+'.txt').render(params)
            html = get_template(spec['template']+'.html').render(params)
            msg = EmailMultiAlternatives(
                spec['subject'],     # Subject
                text,                # Text content
                spec['sender'],      # From
                spec['recipients'],  # To list
                spec['bccs'],        # BCC list
            )
            msg.attach_alternative(html, "text/html")
            msg.send()
            self.logger.info(spec['info-for-log'])
            return True

        except Exception as e:
            # TODO: Save in DB, log error, and try again later?
            self.logger.error("Failed to send email for {} #{} using {} because: {}".format(
                type(obj), getattr(obj, 'pk', "noPK"), type(self), str(e)
            ))
            return False


def register(model_class):
    def x(mailview_class):
        registrations[model_class] = mailview_class
        return mailview_class
    return x

