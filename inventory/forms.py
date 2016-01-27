from django import forms
from django.contrib.auth import authenticate
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML, Div, Field
from datetime import datetime


class Desktop_RequestPermitForm(forms.Form):

    id_verify = forms.BooleanField(
        label="")  # This is a dynamic label which will be set in __init__

    agree_to_terms_1 = forms.BooleanField(
        label="Xerocraft is not responsible for this item at any time including while it is stored at their facility.")

    agree_to_terms_2 = forms.BooleanField(
        label="I shall make a goodwill effort to store the item safely while it is at Xerocraft's facility.")

    agree_to_terms_3 = forms.BooleanField(
        label="If the permit is not renewed every 30 days, the item may be considered abandoned and will be disposed of or claimed by another member.")

    owner_email = forms.EmailField(
        initial="",  # This is a dynamic value which will be set in __init__
        label="Owner's email address: ")

    short_desc = forms.CharField(max_length=80,
        label="Please give a short description of the item: ")

    ok_to_move = forms.TypedChoiceField(widget=forms.RadioSelect,
        coerce=int,
        label="If Xerocraft needs to move this item, we should: ",
        choices=(
            (1,"Go ahead and carefully move it."),
            (0,"Try to contact you before moving it.")))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('request', None).user
        most_formal_name = user.username
        if user.first_name is not None and user.last_name is not None:
            most_formal_name = "{} {}".format(user.first_name, user.last_name)
        self.base_fields['id_verify'].label = "I am {}".format(most_formal_name)
        self.base_fields['owner_email'].initial = "" if user.email is None else user.email
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'id_verify',
            HTML("<p class='agree'>I agree to the following terms and conditions:</p>"),
            Div(
                'agree_to_terms_1',
                'agree_to_terms_2',
                'agree_to_terms_3',
                css_class="terms"
            ),
            'owner_email',
            'short_desc',
            'ok_to_move',
            Submit('submit', 'Submit', css_class='button white'),
        )
        super(Desktop_RequestPermitForm, self).__init__(*args, **kwargs)


class Desktop_ApprovePermitForm(forms.Form):

    approving_member_id = forms.CharField(max_length=50,
        label="Approving Member's U or E: ")

    approving_member_pw = forms.CharField(widget=forms.PasswordInput(),
        label="Approving Member's Password: ")

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Field('approving_member_id', placeholder="Approver's Username or Email"),
                Field('approving_member_pw', placeholder="Approver's Password"),
                css_class="approval",
            ),
            Div(
                Submit('submit', 'Submit', css_class='button white'),
                css_class="submit"
            )
        )
        super(Desktop_ApprovePermitForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(Desktop_ApprovePermitForm, self).clean()
        approving_member_id = cleaned_data.get('approving_member_id')
        approving_member_pw = cleaned_data.get('approving_member_pw')
        approving_member = authenticate(username=approving_member_id, password=approving_member_pw)
        if approving_member is None:
            self.add_error('approving_member_id', "Approver's id or pw is incorrect.")
        # TODO: How to get username, below?
        # elif approving_member.username == <SESSION.USER.USERNAME>:
        #     self.add_error('approving_member_id', "Owner cannot be the approver.")