
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from members.models import Member, Tag, Tagging

from datetime import date

from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderPDF
from reportlab.lib.units import inch, mm
from reportlab.lib.pagesizes import letter

import base64
import uuid
import hashlib


#TODO: Delete _user_info, rename _user_info_2 to _user_info, and adjust calling code.
def _user_info(member_id):
    data = {}
    m = Member.objects.get(pk=member_id)
    data['pk'] = member_id
    data['is_active'] = m.is_active
    data['username'] = m.username
    data['first_name'] = m.first_name
    data['last_name'] = m.last_name
    data['email'] = m.email
    data['tags'] = [t.name for t in m.tags.all()]
    return data


def _user_info_2(member_card_str, staff_card_str):

    member_card_md5 = hashlib.md5(member_card_str.encode()).hexdigest()
    staff_card_md5 = hashlib.md5(staff_card_str.encode()).hexdigest()

    try:
        member = Member.objects.get(membership_card_md5=member_card_md5)
    except Member.DoesNotExist:
        return False, "Invalid staff card"
    try:
        staff = Member.objects.get(membership_card_md5=staff_card_md5)
    except Member.DoesNotExist:
        return False, "Invalid staff card"

    if "Staff" not in [x.name for x in staff.tags.all()]:
        return False, "Not a staff member"

    data = {}
    data['pk'] = member.pk
    data['is_active'] = member.is_active
    data['username'] = member.username
    data['first_name'] = member.first_name
    data['last_name'] = member.last_name
    data['email'] = member.email
    data['tags'] = member.tags.all()
    return True, (member, staff, data)


def tags_for_member_pk(request, member_id):
    return JsonResponse(_user_info(member_id))


def read_membership_card(request, membership_card_str):
    """
    Respond with corresponding user/member info given the membership card string in the QR code.

    :param request: The http request.
    :param qr_code_string: 32 character base64 string from the membership card's QR code.
    :return: JSON encoded info about the member/user or an indication that the qr code data was invalid.
    """

    # TODO: Log validation requests and results?

    membership_card_md5 = hashlib.md5(membership_card_str.encode()).hexdigest()

    try:
        m = Member.objects.get(membership_card_md5=membership_card_md5)
        return JsonResponse(_user_info(m.pk))
    except Member.DoesNotExist:
        return JsonResponse({'error':'No matching membership.'})


@login_required
def create_membership_card(request):

    filename = "member_card_%s.pdf" % request.user.username

    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    member = request.user.member

    b64 = member.generate_member_card_str()

    # Produce PDF using ReportLab:
    p = canvas.Canvas(response, pagesize=letter)
    pageW, pageH = letter

    # Business card size is 2" x 3"
    # Credit card size is 2.2125" x 3.370"
    card_width = 2.125*inch
    card_height = 3.370*inch
    card_corner_r = 3.0*mm

    refX = pageW/2.0
    refY = 7.25*inch

    # Some text to place near the top of the page.
    p.setFont("Helvetica", 16)
    p.drawCentredString(refX, refY+3.00*inch, 'This is your new Xerocraft membership card.')
    p.drawCentredString(refX, refY+2.75*inch, 'Always bring it with you when you visit Xerocraft.')
    p.drawCentredString(refX, refY+2.50*inch, 'The rectangle is credit card sized, if you would like to cut it out.')
    p.drawCentredString(refX, refY+2.25*inch, 'If you have any older cards, they have been deactivated.')

    # Changing refY allows the following to be moved up/down as a group, w.r.t. the text above.
    refY -= 0.3*inch

    # Most of the wallet size card:
    p.roundRect(refX-card_width/2, refY-1.34*inch, card_width, card_height, card_corner_r)
    p.setFont("Helvetica", 21)
    p.drawCentredString(refX, refY-0.3*inch, 'XEROCRAFT')
    p.setFontSize(16)
    p.drawCentredString(refX, refY-0.65*inch, member.first_name)
    p.drawCentredString(refX, refY-0.85*inch, member.last_name)
    p.setFontSize(12)
    p.drawCentredString(refX, refY-1.2 *inch, date.today().isoformat())

    # QR Code:
    qr = QrCodeWidget(b64)
    qrSide = 2.3*inch # REVIEW: This isn't actually 2.3 inches.  What is it?
    bounds = qr.getBounds()
    qrW = bounds[2] - bounds[0]
    qrH = bounds[3] - bounds[1]
    drawing = Drawing(1000,1000,transform=[qrSide/qrW, 0, 0, qrSide/qrH, 0, 0])
    drawing.add(qr)
    renderPDF.draw(drawing, p, refX-qrSide/2, refY-0.19*inch)

    p.showPage()
    p.save()
    return response


def kiosk_waiting(request):
    return render(request, 'members/kiosk-waiting.html',{})


def kiosk_check_in_member(request, member_card_str):

    member_card_md5 = hashlib.md5(member_card_str.encode()).hexdigest()
    try:
        m = Member.objects.get(membership_card_md5=member_card_md5)
    except Member.DoesNotExist:
        return render(request, 'members/kiosk-invalid-card.html',{})

    # TODO: Inform Kyle's system of check-in.
    return render(request, 'members/kiosk-check-in-member.html',{"username" : m.username})


def kiosk_member_details(request, member_card_str, staff_card_str):
    member_card_md5 = hashlib.md5(member_card_str.encode()).hexdigest()
    staff_card_md5 = hashlib.md5(staff_card_str.encode()).hexdigest()
    try:
        member = Member.objects.get(membership_card_md5=member_card_md5)
        staff = Member.objects.get(membership_card_md5=staff_card_md5)
    except Member.DoesNotExist:
        return render(request, 'members/kiosk-invalid-card.html', {})

    if "Staff" in [x.name for x in staff.tags.all()]:

        member_tags = member.tags.all()
        staff_can_tags = [ting.tag for ting in Tagging.objects.filter(can_tag=True,tagged_member=staff)]
        # staff member can't add tags that member already has, so:
        for tag in member_tags:
            if tag in staff_can_tags:
                staff_can_tags.remove(tag)

        return render(request, 'members/kiosk-member-details.html',{
            "staff_fname" : staff.first_name,
            "memb_fname" : member.first_name,
            "memb_name" : "%s %s" % (member.first_name, member.last_name),
            "username" : member.username,
            "email" : member.email,
            "members_tags" : member_tags,
            "staff_can_tags" : staff_can_tags,
        })
    else:
        return render(request, 'members/kiosk-not-staff.html', {
            "name" : "%s %s" % (staff.first_name, staff.last_name),
        })


def kiosk_add_tag(request, member_card_str, staff_card_str, tag_pk):
    # We only get to this view from a link produced by a previous view.
    # This view assumes that the previous view is passing valid strs and pk.
    # Any exceptions raised in this view can be considered programming errors and are not caught.
    # This view DOES NOT use member PKs even though the previous view could provide them.
    # Using PKs would make this view vulnerable to brute force attacks to create unauthorized taggings.

    member_card_md5 = hashlib.md5(member_card_str.encode()).hexdigest()
    staff_card_md5 = hashlib.md5(staff_card_str.encode()).hexdigest()

    member = Member.objects.get(membership_card_md5=member_card_md5)
    staff = Member.objects.get(membership_card_md5=staff_card_md5)

    tag = Tag.objects.get(pk=tag_pk)

    # The following can be considered an assertion that the given staff member is authorized to grant the given tag.
    Tagging.objects.get(can_tag=True,tagged_member=staff,tag=tag)

    # Create the new tagging and then go back to the member details view.
    Tagging.objects.create(tagged_member=member, authorizing_member=staff, tag=tag)
    return redirect('..')
