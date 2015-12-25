from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate

from inventory.models import PermitScan, ParkingPermit, Location
from inventory.forms import *
from members.models import Member

from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderPDF
from reportlab.lib.units import inch
from reportlab.rl_config import defaultPageSize

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def respond_with_permit_pdf(permit):
    """
    :param permit: The permit for which to generate the PDF
    :return: An HTTP response
    """
    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="permit_%05d.pdf"' % permit.pk

    # Produce PDF using ReportLab:
    p = canvas.Canvas(response)
    pageW = defaultPageSize[0]
    pageH = defaultPageSize[1]
    refX = pageW/2
    refY = pageH - 6.25*inch

    # The tag that gets placed near the location.
    p.rect(refX-2.0*inch, refY-0*inch, 4*inch, 5*inch)

    refY += 4.5*inch

    # Static header:
    p.setFont("Helvetica", 14)
    p.drawCentredString(refX, refY-0.00*inch, 'XEROCRAFT HACKERSPACE')
    p.setFont("Helvetica-Bold", 28)
    p.drawCentredString(refX, refY-0.40*inch, 'PARKING PERMIT')
    p.setFont("Helvetica", 14)
    p.drawCentredString(refX, refY-0.66*inch, 'MEMBER-CLAIMED PROPERTY')

    # Changing refY allows the follwoing to be moved up/down as a group, w.r.t. the text above.
    refY -= 3.0*inch

    # QR Code:
    qr = QrCodeWidget('{"permit":%d}' % permit.id)
    qrSide = 2.5*inch # REVIEW: This isn't actually 2.3 inches.  What is it?
    bounds = qr.getBounds()
    qrW = bounds[2] - bounds[0]
    qrH = bounds[3] - bounds[1]
    drawing = Drawing(1000,1000,transform=[qrSide/qrW, 0, 0, qrSide/qrH, 0, 0])
    drawing.add(qr)
    renderPDF.draw(drawing, p, refX-qrSide/2, refY)

    p.setFont("Helvetica", 10)
    p.drawCentredString(refX, refY-0.00*inch, permit.short_desc)
    u = permit.owner.auth_user
    p.drawCentredString(refX, refY-0.20*inch, "Parked by: %s %s" % (u.first_name, u.last_name))
    p.drawCentredString(refX, refY-0.40*inch, "Permit #%05d" % permit.id)

    p.setFont("Helvetica", 14)
    if permit.ok_to_move:
        p.drawCentredString(refX, refY-0.80*inch, "It is OK to carefully move this item")
        p.drawCentredString(refX, refY-1.00*inch, "to another location, if required.")

    else:
        p.drawCentredString(refX, refY-0.80*inch, "This item is fragile. Please attempt")
        p.drawCentredString(refX, refY-1.00*inch, "to contact me before moving it.")

    p.showPage()
    p.save()
    return response


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def _form_to_session(request, form):
    request.session["id_verify"] = form.cleaned_data["short_desc"]
    request.session["agree_to_terms_1"] = form.cleaned_data["agree_to_terms_1"]
    request.session["agree_to_terms_2"] = form.cleaned_data["agree_to_terms_2"]
    request.session["agree_to_terms_3"] = form.cleaned_data["agree_to_terms_3"]
    request.session["short_desc"] = form.cleaned_data["short_desc"]
    request.session["ok_to_move"] = form.cleaned_data["ok_to_move"]
    request.session["owner_email"] = form.cleaned_data["owner_email"]
    request.session["paying_member"] = form.cleaned_data["paying_member"]
    request.session.modified = True


def _session_to_form(request, form):
    form.fields['id_verify'].initial = request.session.get('id_verify', "")
    form.fields['agree_to_terms_1'].initial = request.session.get('agree_to_terms_1', "")
    form.fields['agree_to_terms_2'].initial = request.session.get('agree_to_terms_2', "")
    form.fields['agree_to_terms_3'].initial = request.session.get('agree_to_terms_3', "")
    form.fields['short_desc'].initial = request.session.get('short_desc', "")
    form.fields['ok_to_move'].initial = request.session.get('ok_to_move', "")
    form.fields['owner_email'].initial = request.session.get('owner_email', request.user.email)
    form.fields['paying_member'].initial = request.session.get('paying_member', "")


def _clear_session(request):
    del request.session["id_verify"]
    del request.session["agree_to_terms_1"]
    del request.session["agree_to_terms_2"]
    del request.session["agree_to_terms_3"]
    del request.session["short_desc"]
    del request.session["ok_to_move"]
    del request.session["owner_email"]
    del request.session["paying_member"]
    del request.session["approving_member_username"]
    request.session.modified = True

@login_required
def desktop_request_parking_permit(request):
    """Present a form with parking Ts&Cs and inputs for info about parked item."""

    if request.method == 'POST':
        form = Desktop_RequestPermitForm(request.POST, request=request)
        if form.is_valid():
            _form_to_session(request, form)
            if request.session.get("paying_member"):
                return redirect('inv:desktop-verify-parking-permit')
            else:
                return redirect('inv:desktop-approve-parking-permit')

    else:  # If a GET (or any other method) we'll create a blank form.
        form = Desktop_RequestPermitForm(request=request)
        request.session["approving_member_username"] = None
        _session_to_form(request, form)

    return render(request, 'inventory/desktop-parking-permit-request.html', {'form': form})


@login_required
def desktop_approve_parking_permit(request):

    if request.method == 'POST':
        form = Desktop_ApprovePermitForm(request.POST)
        if form.is_valid():
            approving_member_id = form.cleaned_data["approving_member_id"]
            approving_member_pw = form.cleaned_data["approving_member_pw"]
            approving_member = authenticate(username=approving_member_id, password=approving_member_pw)
            request.session["approving_member_username"] = approving_member.username
            return redirect('inv:desktop-verify-parking-permit')

    else:  # If a GET (or any other method) we'll create a blank form.
        form = Desktop_ApprovePermitForm()

    return render(request, 'inventory/desktop-parking-permit-approve.html', {'form': form})

@login_required
def desktop_verify_parking_permit(request):

    if request.method == 'POST':
        owner = request.user
        try:

            # Process the email address the owner provided.
            owner_email = request.session.get("owner_email")
            if owner.email == "":
                owner.email == owner_email
                owner.save()
            elif owner.email != owner_email:
                pass
                # TODO: Save as an alternate email (member app) and log as a WARNING or INFO?

            # Create the parking permit in the database
            perm = ParkingPermit.objects.create(
                owner = request.user.member,
                short_desc = request.session.get("short_desc"),
                ok_to_move = request.session.get("ok_to_move"),
                approving_member = Member.get_local_member(request.session.get("approving_member_username"))
            )

            _clear_session(request)
            return HttpResponse("SUCCESS "+str(perm.pk))

        except Exception as e:
            return HttpResponse("ERROR "+str(e))

    else:  # For GET and any other methods:
        return render(request, 'inventory/desktop-parking-permit-verify.html')


def print_parking_permit(request, pk):
    """Generate the PDF of the specified permit. Permit must already exist."""
    permit = get_object_or_404(ParkingPermit, id=pk)
    return respond_with_permit_pdf(permit)


@login_required
def renew_parking_permits(request):
    """Generate an HTML page that allows user to specify permits to be renewed and/or closed."""
    pass  # TODO

# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

def get_parking_permit_details(request, pk):
    """Generate a JSON response that contains:
        1) Permit attributes
        2) List of locs where the permit was scanned
        3) List of renewal dates
     Intended for mobile apps."""

    try:
        permit = ParkingPermit.objects.get(id=pk)
    except ParkingPermit.DoesNotExist:
        return JsonResponse({"error":"Parking Permit does not exist in database."})

    scans = []
    for scan in permit.scans.all():
        who = None if scan.who is None else scan.who.pk
        scans.append({"who":who, "where":scan.where.pk, "when":scan.when})

    renewals = []
    for renewal in permit.renewals.all():
        renewals.append(renewal.when)

    json = {}
    json["permit"] = permit.pk
    json["short_desc"] = permit.short_desc
    json["ok_to_move"] = permit.ok_to_move
    json["owner_pk"] = permit.owner.pk
    json["owner_name"] = str(permit.owner)
    json["created"] = permit.created
    json["is_in_inventoried_space"] = permit.is_in_inventoried_space

    json["scans"] = scans
    json["renewals"] = renewals

    return JsonResponse(json)


def note_parking_permit_scan(request, permit_pk, loc_pk):
    """Record the fact that the specified permit was scanned at the specified location."""

    #TODO: 404 isn't a very friendly response to the app and it reports failure to parse response.
    # Respond with error JSON instead?
    # {"error":"No such parking permit exists in database."} or {"error":"No such location exists in database."}
    # Log odd request?
    permit_scanned = get_object_or_404(ParkingPermit, id=permit_pk)
    location_of_scan = get_object_or_404(Location, id=loc_pk)

    PermitScan.objects.create(
        permit=permit_scanned,
        where=location_of_scan,
        when=timezone.now())

    permit_scanned.is_in_inventoried_space = True

    return JsonResponse({"success":"OK"})

def inventory_todos(request):
    """Generate an HTML page instructing reader which locations most need to be scanned."""
    pass #TODO

def get_location_qrs(request, start_pk):
    """Generate the PDF for the small sign that identifies a location."""

    start_pk = int(start_pk)

    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="locs_from_%04d.pdf"' % start_pk

    # Produce PDF using ReportLab:
    p = canvas.Canvas(response)
    pageW = defaultPageSize[0]
    pageH = defaultPageSize[1]
    marginX = 1.1*inch
    marginY = 1.1*inch
    spacingX = 0*inch
    spacingY = 0*inch
    tagw = 1.0*inch
    tagh = 1.3*inch
    xCount = 7
    yCount = 8
    for y in range(yCount):
        for x in range(xCount):
            centerX = marginX + x*(tagw+spacingX)
            centerY = pageH - (marginY + y*(tagh+spacingY))

            #p.rect(centerX-tagw/2, centerY-tagh/2, tagw, tagh)

            l = centerX - tagw/2
            r = l + tagw
            b = centerY - tagh/2
            t = b + tagh
            m = .05*inch
            p.lines([(l,t-m,l,t),(l,t,l+m,t)])
            p.lines([(l,b+m,l,b),(l,b,l+m,b)])
            p.lines([(r-m,t,r,t),(r,t,r,t-m)])
            p.lines([(r-m,b,r,b),(r,b,r,b+m)])

            loc_pk = start_pk + xCount*y + x
            Location.objects.get_or_create(pk=loc_pk)

            # QR Code:
            qr = QrCodeWidget('{"loc":%d}' % loc_pk)
            bounds = qr.getBounds()
            qrW = bounds[2] - bounds[0]
            qrH = bounds[3] - bounds[1]
            xx = 1.1*tagw
            yy = 1.1*tagw
            drawing = Drawing(xx, yy, transform=[xx/qrW, 0, 0, yy/qrH, 0, 0])
            drawing.add(qr)
            renderPDF.draw(drawing, p, centerX-xx/2, 0.1*inch+centerY-yy/2)

            p.setFont("Helvetica", 16)
            p.drawCentredString(centerX, centerY-.55*inch, "L%04d" % loc_pk)

    p.showPage()
    p.save()
    return response

def list_my_permits(request):
    pass