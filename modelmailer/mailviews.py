
# Standard
import logging

# Third Party
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.db.models import Model

# Local

_registry = {}


# TODO: Constructor should take the object to view.
# This would immediately fetch the spec and produce html and text
class MailView:

    def __init__(self):
        self.logger = logging.getLogger("modelmailer")

    @staticmethod
    def for_model(model):
        return _registry[model]

    def get_email_spec(self, obj):
        raise NotImplementedError("get_email_spec must be implemented by subclass")

    def get_html(self, obj):
        spec = self.get_email_spec(obj)
        params = spec['parameters']
        html = get_template(spec['template'] + '.html').render(params)
        return html

    def send(self, obj: Model):
        try:
            spec = self.get_email_spec(obj)
            params = spec['parameters']
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


def register(model_class: Model):
    def x(mailview_class: MailView):
        _registry[model_class] = mailview_class
        return mailview_class
    return x

