
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from members.models import Member

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


def _user_info(member_id):
    data = {}
    m = Member.objects.get(pk=member_id)
    u = m.auth_user
    data['pk'] = member_id
    data['is_active'] = u.is_active
    data['username'] = u.username
    data['first_name'] = u.first_name
    data['last_name'] = u.last_name
    data['email'] = u.email
    data['tags'] = [t.name for t in m.tags.all()]
    return data


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

    # Generate a membership card string which is 32 characters of url-safe base64.
    u1 = uuid.uuid4().bytes
    u2 = uuid.uuid4().bytes
    b64 = base64.urlsafe_b64encode(u1+u2).decode()[:32]
    md5 = hashlib.md5(b64.encode()).hexdigest()

    # Check for md5 hash collision.
    md5_count = Member.objects.filter(membership_card_md5=md5).count()
    assert md5_count <= 1 # Greater than 1 means collision checking has somehow failed in the past.
    if md5_count > 0:
        # Collision detected, so try again.
        return create_membership_card(request)
    else:
        # Save the the md5 of the base64 string in the member table.
        # Since login is required for this view, User.DoesNotExist will not be thrown.
        user = User.objects.get(username=request.user.username)
        assert user.member is not None
        user.member.membership_card_md5 = md5
        user.member.membership_card_when = timezone.now()
        user.member.save()

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
    p.drawCentredString(refX, refY-0.65*inch, user.first_name)
    p.drawCentredString(refX, refY-0.85*inch, user.last_name)
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
    return render(request, 'members/kiosk-check-in-member.html',{"username" : m.auth_user.username})


def kiosk_member_details(request, member_card_str, staff_card_str):
    member_card_md5 = hashlib.md5(member_card_str.encode()).hexdigest()
    staff_card_md5 = hashlib.md5(staff_card_str.encode()).hexdigest()
    try:
        member = Member.objects.get(membership_card_md5=member_card_md5)
        staff = Member.objects.get(membership_card_md5=staff_card_md5)
    except Member.DoesNotExist:
        return render(request, 'members/kiosk-invalid-card.html', {})

    if "Staff" in [x.name for x in staff.tags.all()]:
        return render(request, 'members/kiosk-member-details.html',{
            "name" : "%s %s" % (member.auth_user.first_name, member.auth_user.last_name),
            "username" : member.auth_user.username,
            "email" : member.auth_user.email,
            "tag_names" : [t.name for t in member.tags.all()],
        })
    else:
        return render(request, 'members/kiosk-not-staff.html', {
            "name" : "%s %s" % (staff.auth_user.first_name, staff.auth_user.last_name),
        })