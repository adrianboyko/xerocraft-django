
# Standard

# Third Party
from django.http import HttpResponse
from django_object_actions import DjangoObjectActions
from django.db.models import Model

# Local
from modelmailer.mailviews import MailView


class ModelMailerAdmin(DjangoObjectActions):

    # TODO: email_action needs to be more elaborate, offering html view, text view
    # and ability to immediately send email message. This is a minimal first step.
    def email_action(self, request, obj: Model):
        mailview_cls = MailView.for_model(type(obj))
        mailview = mailview_cls()
        html = mailview.get_html(obj)
        return HttpResponse(html)

    email_action.label = "Email"
    email_action.short_description = "View/send email representation of object."
    change_actions = ('email_action',)
