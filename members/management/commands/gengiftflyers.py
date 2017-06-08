# Standard
import string
import random
from subprocess import call
from typing import Optional

# Third Party
from django.core.management.base import BaseCommand
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, mm

# Local
from members.models import MembershipGiftCard, MembershipCampaign


class Command(BaseCommand):

    help = "Generate a PDF to print on a flyer that will have gift membership tabs to tear off."

    page_height = 11.0000 * inch
    page_width = 8.5000 * inch
    left_margin = 10 * mm
    bottom_margin = 5 * mm
    tab_height = 2.0000 * inch
    right_margin = left_margin
    top_margin = bottom_margin
    num_tabs = 12

    def add_arguments(self, parser):
        parser.add_argument('prefix', help="A short prefix used to group cards for events, etc.")
        parser.add_argument('price', type=int, help="The price for the tabs being generated.")
        parser.add_argument('campaign', type=int, help="The PK of the campain to link the tab codes to.")
        parser.add_argument('-m', '--months', type=int, help="The number of membership months a tab conveys.")
        parser.add_argument('-d', '--days', type=int, help="The number of membership days a tab conveys.")
        parser.add_argument('--dry-run', action="store_true", default=False, help="Make the PDF but don't create anything in the database.")

    def create_db_entry(self, redemption_code: str) -> Optional[MembershipGiftCard]:
        if self.dry_run:
            return None

        try:
            campaign = MembershipCampaign.objects.get(pk=self.campaign_pk)
            mgc = MembershipGiftCard.objects.create(
                redemption_code=redemption_code,
                campaign=campaign,
                price=self.price,
                month_duration=self.month_duration,
                day_duration=self.day_duration,
            )
            mgc.clean()  # Ensures that it's valid.
            return mgc
        except Exception as e:
            print("ERROR " + str(e))
            raise e

    def generate_redemption_code(self, size=6, chars=string.ascii_uppercase + string.digits) -> str:

        # Not the most secure method, but perfectly adequate for redemption strings on gift cards.
        randstr = ''.join(random.choice(chars) for _ in range(size))
        redemption_code = "{}-{}".format(self.prefix, randstr)

        # Check that redemption code is unique.
        try:
            MembershipGiftCard.objects.get(redemption_code=redemption_code)
            return self.generate_redemption_code()  # It isn't, so try again.
        except MembershipGiftCard.DoesNotExist:
            return redemption_code  # It is, so return it.
        except Exception as e:
            print("ERROR " + str(e))
            raise e

    def draw_tab_bounds(self, c: Canvas, x: float, y: float, tab_width: float):
        p = c.beginPath()
        p.moveTo(x, y)
        p.lineTo(x, y + self.tab_height)
        p.lineTo(x + tab_width, y + self.tab_height)
        p.lineTo(x + tab_width, y)
        p.lineTo(x, y)
        p.close()
        c.drawPath(p)

    def draw_tab_guides(self, c: Canvas, x: float, y: float, tab_width: float):
        g = 1 * mm
        h = self.tab_height
        w = tab_width
        c.setLineWidth(.1*mm)
        c.line(x, y, x, y+g)
        c.line(x+w, y, x+w, y+g)
        c.line(x, y+h, x, y+h-g)
        c.line(x+w, y+h, x+w, y+h-g)
        c.line(x-g, y+h, x+g, y+h)
        c.line(x-g+w, y+h, x+g+w, y+h)

    def draw_tab(self, c: Canvas, tab_num: int, redemption_code: str) -> None:
        tab_width = (self.page_width - self.left_margin - self.right_margin)/self.num_tabs

        # (x,y) is bottom left corner of the tab:
        x = self.left_margin + (tab_num * tab_width)
        y = self.bottom_margin

        # Drawing tab bounds helps when adjusting layout. Not for production.
        #self.draw_tab_bounds(c, x, y, tab_width)
        self.draw_tab_guides(c, x, y, tab_width)

        c.saveState()
        c.translate(x + 0.5 * tab_width, y + 0.5 * self.tab_height)
        c.rotate(90)
        c.setFont("Helvetica", 13)
        c.drawString(-0.47 * self.tab_height, 0.1 * tab_width, "Free Membership!")
        c.setFont("Courier-Bold", 16)
        c.drawString(-0.47 * self.tab_height, -0.25 * tab_width, redemption_code)
        c.restoreState()

        return None

        c.setFont("Helvetica", 10)

        # Space to enter redemption month and day.
        p = c.beginPath()
        p.moveTo(x + 20, y + 12)
        p.lineTo(x + 45, y + 12)
        p.moveTo(x + 55, y + 12)
        p.lineTo(x + 80, y + 12)
        p.close()
        c.drawPath(p)
        c.drawCentredString(x + 15, y + 16, 'm:')
        c.drawCentredString(x + 50, y + 16, 'd:')

        # Space to enter redeemer's email address.
        p = c.beginPath()
        p.moveTo(x - 80, y - 14)
        p.lineTo(x + 80, y - 14)
        p.close()
        c.drawPath(p)
        c.drawCentredString(x, y - 24, 'email address')

    def handle(self, *args, **options):

        self.prefix = options['prefix']
        self.price = options['price']
        self.month_duration = options['months']
        self.day_duration = options['days']
        self.dry_run = options['dry_run']
        self.campaign_pk = options['campaign']

        filename = "flyer_{}.pdf".format(self.prefix)
        c = Canvas(filename, pagesize=letter)
        for tab in range(self.num_tabs):
            redemption_code = self.generate_redemption_code()
            self.create_db_entry(redemption_code)
            self.draw_tab(c, tab, redemption_code)
        c.showPage()
        c.save()

        call(["cat", filename])  # REVIEW: Python instead?
