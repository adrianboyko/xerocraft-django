# Standard
import string
import random
from subprocess import call

# Third Party
from django.core.management.base import BaseCommand
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

# Local
from members.models import MembershipGiftCard


class Command(BaseCommand):

    help = "Email reports of new taggings are sent to members that authorized those taggings."

    # These values are for Avery 8660, Avery 5630, 3M 3500-B, 3M 3400-B, or equivalent.
    page_height   = 11.0000 * inch  # 11"
    page_width    =  8.5000 * inch  # 8+1/2"
    left_margin   =  0.1875 * inch  # 3/16"
    bottom_margin =  0.5000 * inch  # 1/2"
    inner_margin  =  0.1250 * inch  # 1/8" gap between labels in a given row.
    label_height  =  1.0000 * inch  # 1"
    label_width   =  2.6250 * inch  # 2+5/8"

    right_margin  = left_margin
    top_margin = bottom_margin

    def add_arguments(self, parser):
        parser.add_argument('prefix', help="A short prefix used to group cards for events, etc.")
        parser.add_argument('price', type=int, help="The price for the cards being generated.")
        parser.add_argument('-m', '--months', type=int, help="The number of membership months this gift card conveys.")
        parser.add_argument('-d', '--days', type=int, help="The number of membership days this gift card conveys.")
        parser.add_argument('--dry-run', type=bool, default=False, help="Make the PDF but don't create anything in the database.")

    def create_db_entry(self, redemption_code):
        if self.dry_run:
            return

        try:
            mgc = MembershipGiftCard.objects.create(
                redemption_code=redemption_code,
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

    def draw_label_bounds(self, c: Canvas, x, y):
        p = c.beginPath()
        x -= 0.5*self.label_width
        y -= 0.5*self.label_height
        p.moveTo(x, y)
        p.lineTo(x, y + self.label_height)
        p.lineTo(x + self.label_width, y + self.label_height)
        p.lineTo(x + self.label_width, y)
        p.lineTo(x, y)
        p.close()
        c.drawPath(p)

    def draw_label(self, c: Canvas, col: int, row: int, redemption_code: str):
        x = self.left_margin + (col + 0.5) * self.label_width + col * self.inner_margin
        y = self.page_height - self.top_margin - (row + 0.5) * self.label_height

        # Drawing label bounds helps when adjusting layout. Not for production.
        # self.draw_label_bounds(c, x, y)

        c.setFont("Courier-Bold", 13)
        c.drawString(x - 80, y + 14, redemption_code)

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

        c = Canvas("labels.pdf", pagesize=letter)
        for row in range(0, 10):
            for col in range(0, 3):
                redemption_code = self.generate_redemption_code()
                self.create_db_entry(redemption_code)
                self.draw_label(c, col, row, redemption_code)
        c.showPage()
        c.save()

        call(["cat", "labels.pdf"])  # REVIEW: Python instead?
