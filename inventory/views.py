from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from members.models import Member
from inventory.models import PermitScan, ParkingPermit, Location

from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderPDF
from reportlab.lib.units import inch
from reportlab.rl_config import defaultPageSize

def index(request):
    return render(request, 'inventory/inventory-home.html',{})

#TODO: Permit PDF is a little too long. Compare to credit card and fix.
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

@login_required
def request_parking_permit(request):
    """Present a form with parking Ts&Cs and inputs for info about parked item."""

    #TODO: Refuse to create parking permit if user has no fname, lname, or phone#.
    return render(request, 'inventory/request-permit.html',{})


@login_required
def create_parking_permit(request):

    # Since login is required for this view, User.DoesNotExist will not be thrown.
    user = User.objects.get(username=request.user.username)
    assert user.member is not None

    permit = ParkingPermit.objects.create(
        owner = user.member,
        created = timezone.now(),
        short_desc = request.POST["short_desc"],
        ok_to_move = request.POST["move"] == "Y")

    return respond_with_permit_pdf(permit)

def get_parking_permit(request, pk):
    """Generate the PDF of the specified permit. Permit must already exist."""

    permit = get_object_or_404(ParkingPermit, id=pk)
    return respond_with_permit_pdf(permit)

@login_required
def renew_parking_permits(request):
    """Generate an HTML page that allows user to specify permits to be renewed and/or closed."""
    pass #TODO

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
        scans.append({"where":scan.where.pk, "when":scan.when})

    renewals = []
    for renewal in permit.renewals.all():
        renewals.append(scan.when)

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
            #TODO: Create location in DB if it doesn't yet exist.

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