# Standard
from datetime import datetime, date, timedelta, time
from time import sleep
from math import floor
import hashlib
from typing import Optional

# Third Party
from django.core import management, mail
from django.urls import reverse
from django.test import LiveServerTestCase
from django.contrib.auth.models import User
from freezegun import freeze_time
from selenium import webdriver
from selenium.webdriver.firefox.webelement import FirefoxWebElement
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from pyvirtualdisplay import Display
from rest_framework.authtoken import models as tokmod
from django.utils.timezone import make_aware

# Local
from members.models import Member, VisitEvent, Membership
from tasks.models import RecurringTaskTemplate, Claim, TimeAccountEntry, Work


# = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =

class IntegrationTest(LiveServerTestCase):

    display = None  # type: Display
    browser = None  # type: webdriver.Firefox

    EXISTING_USERNAME = "existing"
    EXISTING_RFIDDEC = "888888888"
    EXISTING_RFIDHEX = "34FB5E38"

    WITNESS_USERNAME = "manager"
    WITNESS_PASSWORD = "notapassword"
    WITNESS_RFIDDEC = "777777777"
    WITNESS_RFIDHEX = "2E5BF271"

    SPECIFIC_TASK_SHORT_DESC = "Specific Task"
    OTHER_WORK_SHORT_DESC = "Other Work"
    LONG_TEXT = "This is a test. It is only a test."

    fixtures = ['elm-clients/reception-kiosk/tests/test-integration-fixture.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # cls.display = Display(visible=0, size=(1024, 768))
        # cls.display.start()
        DRIVER = "/usr/local/bin/geckodriver"
        # os.environ["webdriver.firefox.driver"] = DRIVER
        cls.browser = webdriver.Firefox(executable_path=DRIVER)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        # cls.display.stop()
        super().tearDownClass()

    def setUp(self):
        print("")
        print("Setting up...")
        existing_user = {
            'username'  : self.EXISTING_USERNAME,
            'first_name': 'Jane',
            'last_name' : 'Doe',
            'password'  : '123',
            'email'     : 'test@example.com'
        }
        witness_user = {
            'username' : self.WITNESS_USERNAME,
            'password' : self.WITNESS_PASSWORD,
            'email'    : 'witness@example.com'
        }
        kiosk_user = {
            'username': "ReceptionKiosk1",
            'password': '123',
            'email'   : 'kiosk@example.com'
        }
        self.existing_member = User.objects.create_superuser(**existing_user).member  # type: Member
        self.kiosk_user = User.objects.create_superuser(**kiosk_user)
        self.witness_member = User.objects.create_superuser(**witness_user).member

        self.existing_member.membership_card_md5 = self.EXISTING_RFIDDEC
        self.existing_member.clean()  # This will cause the memb card to be md5 encoded.
        self.existing_member.save()  # So save the modification...
        self.existing_member.refresh_from_db()  # And reload the member.

        self.witness_member.membership_card_md5 = self.WITNESS_RFIDDEC
        self.witness_member.clean()  # This will cause the memb card to be md5 encoded.
        self.witness_member.save()  # So save the modification...
        self.witness_member.refresh_from_db()  # And reload the member.

        tokmod.Token.objects.create(
            key="testkiosk",
            user=self.kiosk_user
        )

        self.createTasks(self.SPECIFIC_TASK_SHORT_DESC, self.existing_member, False)
        self.createTasks(self.OTHER_WORK_SHORT_DESC, None, True)

    @classmethod
    def createTasks(cls,
     short_desc: str, default_claimant: Optional[Member], anybody_is_eligible: bool):
        template = RecurringTaskTemplate.objects.create(
            short_desc=short_desc,
            max_work=timedelta(hours=1.0),
            start_date=date.today(),
            work_start_time=time(18, 00),
            work_duration=timedelta(hours=1.5),
            repeat_interval=1,
            default_claimant=default_claimant,
            should_nag=True,
            priority=RecurringTaskTemplate.PRIO_HIGH
        )
        if default_claimant is not None:
            template.eligible_claimants.add(default_claimant)
        template.anybody_is_eligible = anybody_is_eligible
        template.save()
        template.full_clean()
        management.call_command("scheduletasks", "1")

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def findTagContaining(self, tagname: str, content: str) -> FirefoxWebElement:
        try:
            self.browser.implicitly_wait(10)
            xpath = '//{}[contains(.,"{}")]'.format(tagname, content)
            return self.browser.find_element_by_xpath(xpath)
        except NoSuchElementException as e:
            self.fail(e.msg)

    def findSingleTag(self, tagname: str) -> FirefoxWebElement:
        try:
            self.browser.implicitly_wait(10)
            xpath = '//{}'.format(tagname)
            return self.browser.find_element_by_xpath(xpath)
        except NoSuchElementException as e:
            self.fail(e.msg)

    def clickTagContaining(self, tagname: str, content: str) -> None:
        try:
            element = self.findTagContaining(tagname, content)
            element.click()
        except NoSuchElementException as e:
            self.fail(e.msg)

    def findInputWithId(self, id: str) -> FirefoxWebElement:
        try:
            self.browser.implicitly_wait(10)
            return self.browser.find_element_by_id(id)
        except NoSuchElementException as e:
            self.fail(e.msg)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    REASON_CLASS   = "Attending a class or workshop"
    REASON_LOOKING = "Checking out Xerocraft"
    REASON_CLUB    = "Club activity (FRC, VEX, PEC)"
    REASON_GUEST   = "Guest of a paying member"
    REASON_OTHER   = "Other"
    REASON_MEMBER  = "Personal project"
    REASON_WORK    = "Volunteering or staffing"

    # Simple reasons are those that go straight to the CheckInDone scene.
    simple_reasons = [
        REASON_CLASS,
        REASON_CLUB,
        REASON_GUEST,
        REASON_LOOKING,
        REASON_OTHER
    ]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # ASSERTIONS
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def assert_on_CheckInDone(self) -> None:
        self.findTagContaining("p", "You're Checked In")

    def assert_on_CheckIn(self) -> None:
        self.findTagContaining("p", "Let's Get You Checked-In!")

    def assert_on_CheckOutDone(self) -> None:
        self.findTagContaining("p", "You're Checked Out")
        # Because some tests make assertions about VisitEvents after getting to CheckOutDone,
        # and because CheckOutDone's "Ok" button doesn't appear until its VisitEvent
        # has been logged, this assertion will wait for the "Ok" button to appear:
        self.findTagContaining("button", "Ok")

    def assert_on_CheckOut(self) -> None:
        self.findTagContaining("p", "Tap Your Userid, Below")

    def assert_on_CreatingAcct(self) -> None:
        self.findTagContaining("p", "Creating Your Account!")
        self.findTagContaining("p", "One moment please")

    def assert_on_EmailInUse(self) -> None:
        self.findTagContaining("p", "Already Registered!")

    def assert_on_HowDidYouHear(self) -> None:
        self.findTagContaining("p", "Just Wondering")
        self.findTagContaining("p", "How did you hear about us?")

    def assert_on_RfidProblem(self) -> None:
        # NOTE: This is actually the view for the RfidHelper module.
        self.findTagContaining("p", "RFID Problem")

    def assert_on_MembersOnly(self) -> None:
        self.findTagContaining("p", "Supporting Members Only")
        self.findTagContaining("p", "Is your supporting membership up to date?")

    def assert_on_MembersOnly_PayNow(self) -> None:
        self.findTagContaining("div", "We accept credit card, cash, and checks.")

    def assert_on_MembersOnly_SentEmail(self) -> None:
        self.findTagContaining("div", "We've sent payment information to you via email!")

    def assert_on_NewMember(self) -> None:
        self.findTagContaining("p", "Let's Create an Account!")
        self.findTagContaining("p", "Please tell us about yourself:")

    def assert_on_NewUser(self) -> None:
        self.findTagContaining("p", "Login Details")
        self.findTagContaining("p", "Choose an id and password for our website:")

    def assert_on_OldBusiness(self) -> None:
        self.findTagContaining("p", "Let's Review Them")

    def assert_on_ReasonForVisit(self) -> None:
        self.findTagContaining("p", "Today's Activity")

    def assert_on_SignUpDone(self) -> None:
        self.findTagContaining("p", "Xerocraft Account Created!")
        self.findTagContaining("p", "Just one more thing...")

    def assert_on_Start(self) -> None:
        self.findTagContaining("h1", "Welcome!")

    def assert_on_TaskInfo(self) -> None:
        self.findTagContaining("p", "Thanks for Helping!")

    def assert_on_TaskList(self) -> None:
        self.findTagContaining("p", "Choose a Task")

    def assert_on_TimeSheetPt1(self) -> None:
        self.findTagContaining("p", "Let us know how long you worked!")

    def assert_on_TimeSheetPt2(self) -> None:
        self.findTagContaining("p", "Please describe the work you did")

    def assert_on_TimeSheetPt3(self) -> None:
        self.findTagContaining("p", "Do you need this work to be witnessed?")

    def assert_on_Waiver(self) -> None:
        self.findTagContaining("p", "Please read and sign the following waiver")

    def assert_on_Welcome(self) -> None:
        self.findTagContaining("p", "Welcome!")
        self.findTagContaining("p", "Choose one of the following:")

    def assert_on_WelcomeForRfid(self, friendly_name:str) -> None:
        self.findTagContaining("p", "Welcome {}!".format(friendly_name))
        self.findTagContaining("p", "Choose one of the following:")

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # SCENE TRANSITIONS
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def backOneScene(self) -> None:
        self.clickTagContaining("button", "Back")

    def checkInDone_to_start(self) -> None:
        self.assert_on_CheckInDone()  # Precondition
        self.clickTagContaining("button", "Ok")
        self.assert_on_Start()  # Postcondition

    def checkIn_to_reasonForVisit_viaFlexId(self, flexid: str, username: str) -> None:
        self.assert_on_CheckIn()  # Precondition
        self.findInputWithId("[100,1]").send_keys(flexid+Keys.ENTER)
        self.clickTagContaining("button", username)
        self.assert_on_ReasonForVisit()  # Postcondition

    def checkIn_to_reasonForVisit_viaRfid(self, rfidstr: str) -> None:
        self.assert_on_CheckIn()  # Precondition
        self.findSingleTag("body").send_keys(">"+rfidstr)
        self.assert_on_ReasonForVisit() # Postcondition

    def checkIn_to_rfidProblem_viaRfid(self, rfidstr: str) -> None:
        self.assert_on_CheckIn()  # Precondition
        self.findSingleTag("body").send_keys(">"+rfidstr)
        self.assert_on_RfidProblem()  # Postcondition

    def checkOutDone_to_start(self) -> None:
        self.assert_on_CheckOutDone()  # Precondition
        self.clickTagContaining("button", "Ok")
        self.assert_on_Start()  # Postcondition

    def checkOut_to_next_viaRfid(self, rfidstr: str) -> None:
        self.assert_on_CheckOut()  # Precondition
        self.findSingleTag("body").send_keys(">"+rfidstr)
        # NOTE: NO POSTCONDITION

    def checkOut_to_next_viaUname(self, username: str) -> None:
        self.assert_on_CheckOut()  # Precondition
        self.clickTagContaining("button", username)
        # NOTE: NO POSTCONDITION

    def emailInUse_to_checkIn(self) -> None:
        self.assert_on_EmailInUse()  # Precondition
        self.clickTagContaining("button", "Check In")
        self.assert_on_CheckIn()  # Postcondition

    def emailInUse_to_start(self) -> None:
        self.assert_on_EmailInUse()  # Precondition
        self.clickTagContaining("button", "OK")
        self.assert_on_Start()  # Postcondition

    def howDidYouHear_to_newMember_viaDM(self, discoveryMethod: str) -> None:
        self.assert_on_HowDidYouHear()  # Precondition
        self.clickTagContaining("span", discoveryMethod)
        self.clickTagContaining("button", "OK")
        self.assert_on_NewMember() # Postcondition

    def load_to_start(self, time_shift:int=0) -> None:
        # Note: No precondition.
        url = self.live_server_url + reverse('memb:reception-kiosk-timeshift', args=[time_shift])
        self.browser.get(url)
        self.assert_on_Start()  # Postcondition

    def newMember_to_next_viaInfo(self, fname: str, lname: str, email: str, adult:bool) -> None:
        self.assert_on_NewMember()  # Precondition
        self.findInputWithId("[1000,3]").send_keys(fname+Keys.ENTER)
        self.findInputWithId("[1000,4]").send_keys(lname+Keys.ENTER)
        self.findInputWithId("[1000,5]").send_keys(email+Keys.ENTER)
        if adult:
            self.findTagContaining("span", "I'm aged 18 or older").click()
        else:
            self.findTagContaining("span", "I'm younger than 18").click()
        self.findTagContaining("button", "OK").click()
        # TODO: Test that we're on one of the possible "next scenes", as postcondition.

    def newUser_to_waiver_viaIdPw(self, uname: str, pw: str) -> None:
        self.assert_on_NewUser()  # Precondition
        self.findInputWithId("[1100,1]").send_keys(uname+Keys.ENTER)
        self.findInputWithId("[1100,2]").send_keys(pw+Keys.ENTER)
        self.findInputWithId("[1100,3]").send_keys(pw+Keys.ENTER)
        self.clickTagContaining("button", "OK")
        self.assert_on_Waiver()  # Postcondition

    def oldBusiness_to_next_viaDelete(self, taskname: str) -> None:
        self.assert_on_OldBusiness()  # Precondition
        self.clickTagContaining("span", taskname)
        self.clickTagContaining("button", "Delete")
        # TODO: Test that we're on one of the possible "next scenes", as postcondition.

    def oldBusiness_to_next_viaSkip(self) -> None:
        self.assert_on_OldBusiness()  # Precondition
        self.clickTagContaining("button", "Skip")
        # TODO: Test that we're on one of the possible "next scenes", as postcondition.

    def oldBusiness_to_timeSheetPt1_viaTaskName(self, taskname: str) -> None:
        self.assert_on_OldBusiness()  # Precondition
        self.clickTagContaining("span", taskname)
        self.clickTagContaining("button", "Finish")
        self.assert_on_TimeSheetPt1()  # Postcondition

    def reasonForVisit_to_next_viaReason(self, reason: str) -> None:
        self.assert_on_ReasonForVisit()  # Precondition
        self.clickTagContaining("span", reason)
        self.clickTagContaining("button", "OK")
        # TODO: Test that we're on one of the possible "next scenes", as postcondition.

    def signUpDone_to_checkIn(self) -> None:
        self.assert_on_SignUpDone()  # Precondition
        self.clickTagContaining("button", "Check In")
        self.assert_on_CheckIn()  # Postcondition

    def start_to_rfidProblem_viaRfid(self, rfidstr: str) -> None:
        self.assert_on_Start()  # Precondition
        sleep(1)  # REVIEW: Why is this necessary?
        self.findSingleTag("body").send_keys(">"+rfidstr)
        self.assert_on_RfidProblem()  # Postcondition

    def start_to_welcome(self) -> None:
        self.assert_on_Start()  # Precondition
        sleep(1)  # REVIEW: Why is this necessary?
        body = self.browser.find_element_by_tag_name("body")
        body.click()
        self.assert_on_Welcome()  # Postcondition

    def start_to_welcomeForRfid_viaRfid(self, rfidstr: str, friendly_name: str) -> None:
        self.assert_on_Start()  # Precondition
        sleep(1)  # REVIEW: Why is this necessary?
        self.findSingleTag("body").send_keys(">"+rfidstr)
        self.assert_on_WelcomeForRfid(friendly_name)  # Postcondition

    def taskInfo_to_checkInDone(self) -> None:
        self.assert_on_TaskInfo()  # Precondition
        self.clickTagContaining("button", "Got It!")
        self.assert_on_CheckInDone()  # Postcondition

    def taskList_to_taskInfo_viaTaskName(self, taskname: str) -> None:
        self.assert_on_TaskList()  # Preconditon
        self.clickTagContaining("span", taskname)
        self.clickTagContaining("button", "OK")
        self.assert_on_TaskInfo()  # Postcondition

    def taskList_to_taskInfo_viaDefault(self) -> None:
        self.assert_on_TaskList()  # Preconditon
        # TODO: Following sleep can be eliminated by waiting for an element with a selected style.
        sleep(5)  # Need time for today's tasks to arrive and for one to be selected.
        self.clickTagContaining("button", "OK")
        self.assert_on_TaskInfo()  # Postcondition

    def timeSheetPt1_to_next(self) -> None:
        self.assert_on_TimeSheetPt1()  # Precondition
        self.clickTagContaining("button", "2")
        self.clickTagContaining("button", "00")
        self.clickTagContaining("button", "Submit")
        # TODO: Test that we're on one of the possible "next scenes", as postcondition.

    def timeSheetPt2_to_timeSheetPt3_viaDesc(self, workdesc: str) -> None:
        self.assert_on_TimeSheetPt2()  # Precondition
        self.findInputWithId("[1900,1]").send_keys(workdesc+Keys.ENTER)
        self.clickTagContaining("button", "Continue")
        self.assert_on_TimeSheetPt3()  # Postcondition

    def timeSheetPt3_to_next_viaIdPw(self, uname: str, pw: str) -> None:
        self.assert_on_TimeSheetPt3()
        self.clickTagContaining("button", "Witness")
        self.findInputWithId("[2000,1]").send_keys(uname+Keys.ENTER)
        self.findInputWithId("[2000,2]").send_keys(pw+Keys.ENTER)
        self.clickTagContaining("button", "Witness")

    def timeSheetPt3_to_next_viaRfid(self, rfidstr: str):
        self.assert_on_TimeSheetPt3()
        self.findSingleTag("body").send_keys(">"+rfidstr)

    def waiver_to_creatingAcct(self) -> None:
        self.assert_on_Waiver()  # Precondition
        self.clickTagContaining("button", "Sign")
        self.clickTagContaining("button", "Accept")
        self.assert_on_CreatingAcct()  # Postcondition

    def welcomeForRfid_to_reasonForVisit_viaCheckIn(self, friendly_name: str) -> None:
        self.assert_on_WelcomeForRfid(friendly_name)  # Precondition
        self.clickTagContaining("button", "Check In")
        self.assert_on_ReasonForVisit()  # Postcondition

    def welcomeForRfid_to_next_viaCheckOut(self, friendly_name: str) -> None:
        self.assert_on_WelcomeForRfid(friendly_name)  # Precondition
        self.clickTagContaining("button", "Check Out")
        # Postcondition

    def welcome_to_checkIn(self) -> None:
        self.assert_on_Welcome()  # Precondition
        self.clickTagContaining("button", "Check In")
        self.assert_on_CheckIn()  # Postcondition

    def welcome_to_checkOut(self) -> None:
        self.assert_on_Welcome()  # Precondition
        self.clickTagContaining("button", "Check Out")
        self.assert_on_CheckOut()  # Postcondition

    def welcome_to_howDidYouHear(self) -> None:
        self.assert_on_Welcome()  # Precondition
        self.clickTagContaining("button", "I'm new!")
        self.assert_on_HowDidYouHear()  # Postcondition

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # TESTS
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_checkOutWithRfidButWitnessWithKeyboard(self):

        print("Check out with RFID but witness with keyboard")
        workers_friendly_name = self.existing_member.first_name

        # Check IN and start work on task
        self.load_to_start()
        self.start_to_welcomeForRfid_viaRfid(self.EXISTING_RFIDHEX, workers_friendly_name)
        self.welcomeForRfid_to_reasonForVisit_viaCheckIn(workers_friendly_name)
        self.reasonForVisit_to_next_viaReason(self.REASON_WORK)
        self.taskList_to_taskInfo_viaDefault()
        self.taskInfo_to_checkInDone()
        self.checkInDone_to_start()

        # Check OUT and finish task
        # Note: We're already on start scene
        self.start_to_welcomeForRfid_viaRfid(self.EXISTING_RFIDHEX, workers_friendly_name)
        self.welcomeForRfid_to_next_viaCheckOut(workers_friendly_name)
        self.oldBusiness_to_timeSheetPt1_viaTaskName(self.SPECIFIC_TASK_SHORT_DESC)
        self.timeSheetPt1_to_next()
        # Should land us on Pt3
        self.timeSheetPt3_to_next_viaIdPw(self.WITNESS_USERNAME, self.WITNESS_PASSWORD)
        # Should take us to CheckOutDone
        self.assert_on_CheckOutDone()
        self.assertEqual(Work.objects.filter(witness=self.witness_member).count(), 1)


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_witnessWithRfid(self):

        print("Witness with RFID")
        workers_friendly_name = self.existing_member.first_name

        # Check IN and start work on task
        self.load_to_start()
        self.start_to_welcomeForRfid_viaRfid(self.EXISTING_RFIDHEX, workers_friendly_name)
        self.welcomeForRfid_to_reasonForVisit_viaCheckIn(workers_friendly_name)
        self.reasonForVisit_to_next_viaReason(self.REASON_WORK)
        self.taskList_to_taskInfo_viaDefault()
        self.taskInfo_to_checkInDone()
        self.checkInDone_to_start()

        # Check OUT and finish the work in progress
        # Note: We're already on start scene
        self.start_to_welcomeForRfid_viaRfid(self.EXISTING_RFIDHEX, workers_friendly_name)
        self.welcomeForRfid_to_next_viaCheckOut(workers_friendly_name)
        self.oldBusiness_to_timeSheetPt1_viaTaskName(self.SPECIFIC_TASK_SHORT_DESC)
        self.timeSheetPt1_to_next()  # Will go to Pt3
        self.timeSheetPt3_to_next_viaRfid("DEADBEEF")  # Will go to RfidProblem
        self.assert_on_RfidProblem()
        self.backOneScene()
        self.timeSheetPt3_to_next_viaRfid(self.WITNESS_RFIDHEX)
        self.assert_on_CheckOutDone()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_RfidAtCheckInScene(self):
        print("RFID at Check In Scene")

        # Valid RFID CheckIn
        print("  Valid Check In")
        self.assertEqual(VisitEvent.objects.all().count(), 0)
        self.load_to_start()
        self.start_to_welcome()
        self.welcome_to_checkIn()
        self.checkIn_to_reasonForVisit_viaRfid(self.EXISTING_RFIDHEX)
        sleep(2)  # VE is being logged asynchronously, in the background, so give it some time to finish.
        # Check in has not been completed, but there should be a PRESENT VE from the RFID read:
        self.assertEqual(VisitEvent.objects.filter(event_type=VisitEvent.EVT_PRESENT).count(), 1)

        # Invalid RFID CheckIn
        print("  Invalid Check In")
        self.assertEqual(VisitEvent.objects.all().count(), 1)  # I.e. no change.
        self.load_to_start()
        self.start_to_welcome()
        self.welcome_to_checkIn()
        self.checkIn_to_rfidProblem_viaRfid("DEADBEEF")
        self.assertEqual(VisitEvent.objects.all().count(), 1)  # I.e. no change.

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_RfidAtCheckOutScene(self):
        print("RFID at Check Out Scenes")

        # Valid RFID CheckOut
        print("  Valid Check Out")
        self.assertEqual(VisitEvent.objects.all().count(), 0)
        self.load_to_start()
        self.start_to_welcome()
        self.welcome_to_checkOut()
        self.checkOut_to_next_viaRfid(self.EXISTING_RFIDHEX)
        self.assert_on_CheckOutDone()
        # Check out was completed, so there should be PRESENT & DEPARTURE VEs:
        self.assertEqual(VisitEvent.objects.filter(event_type=VisitEvent.EVT_PRESENT).count(), 1)
        self.assertEqual(VisitEvent.objects.filter(event_type=VisitEvent.EVT_DEPARTURE).count(), 1)

        # Invalid RFID CheckOut
        print("  Invalid Check Out")
        self.assertEqual(VisitEvent.objects.all().count(), 2)  # I.e. no change.
        self.load_to_start()
        self.start_to_welcome()
        self.welcome_to_checkOut()
        self.checkOut_to_next_viaRfid("DEADBEEF")
        self.assert_on_RfidProblem()
        self.assertEqual(VisitEvent.objects.all().count(), 2)  # I.e. no change.

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_RfidAtStartScene(self):
        print("RFID at Start Scene")

        friendly_name = self.existing_member.first_name

        # Valid RFID
        self.load_to_start()
        self.start_to_welcomeForRfid_viaRfid(self.EXISTING_RFIDHEX, friendly_name)
        self.welcomeForRfid_to_reasonForVisit_viaCheckIn(friendly_name)
        self.backOneScene()
        self.welcomeForRfid_to_next_viaCheckOut(friendly_name)
        self.checkOutDone_to_start()
        # Check out was completed, so there should be PRESENT & DEPARTURE VEs:
        self.assertEqual(VisitEvent.objects.filter(event_type=VisitEvent.EVT_PRESENT).count(), 1)
        self.assertEqual(VisitEvent.objects.filter(event_type=VisitEvent.EVT_DEPARTURE).count(), 1)

        # Invalid RFID
        # Note: We're already at the start screen.
        self.start_to_rfidProblem_viaRfid("DEADBEEF")

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_LegitNewMemberSignup(self):
        print("Legitimate New Member Signup")

        nowSecondsStr = str(floor(datetime.now().timestamp()))
        hex = hashlib.md5(nowSecondsStr.encode()).hexdigest()
        email = "xis+{}@xerocraft.org".format(hex[:12])
        userName = "amb_{}".format(hex[:12])
        self.load_to_start()
        self.start_to_welcome()
        self.welcome_to_howDidYouHear()
        self.howDidYouHear_to_newMember_viaDM("Twitter")
        self.newMember_to_next_viaInfo("Adrian", "Testing", email, True)
        self.assert_on_NewUser()
        self.newUser_to_waiver_viaIdPw(userName, hex[-12:])
        self.waiver_to_creatingAcct()
        # NOTE: CreatingAcct scene automatically segues to SignUpDone scene, on success.
        self.assert_on_SignUpDone()
        sleep(5)
        self.signUpDone_to_checkIn()
        self.checkIn_to_reasonForVisit_viaFlexId(userName, userName)
        self.reasonForVisit_to_next_viaReason(self.REASON_OTHER)
        self.assert_on_CheckInDone()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_BogusNewMemberSignup(self):
        print("Bogus New Member Signup")
        self.load_to_start()
        self.start_to_welcome()
        self.welcome_to_howDidYouHear()
        self.howDidYouHear_to_newMember_viaDM("Twitter")
        self.newMember_to_next_viaInfo("Joe", "Smith", self.existing_member.email, True)
        self.assert_on_EmailInUse()
        self.emailInUse_to_checkIn()  # User thinks about checking in using identified userid.
        self.backOneScene()                   # Changes mind, and goes back to EmailInUse Scene.
        self.emailInUse_to_start()    # Decides that they're confused and need to talk to a staffer.

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_CheckMembersOnlyInfo(self):
        print("Check Members-Only Info")

        def checkin():
            now = make_aware(datetime.now())
            pit = make_aware(datetime(2018, 2, 19, 20, 00, 00))  # During Mon evening members-only block
            time_shift = floor((pit - now).total_seconds())  # type: int
            with freeze_time(pit):
                self.load_to_start(time_shift)
                self.start_to_welcome()
                self.welcome_to_checkIn()
                self.checkIn_to_reasonForVisit_viaFlexId(self.EXISTING_USERNAME, self.EXISTING_USERNAME)
                self.reasonForVisit_to_next_viaReason(self.REASON_MEMBER)
                self.assert_on_MembersOnly()

        buttonText = "Send Me Payment Info"
        print("  "+buttonText)
        checkin()
        before_count = len(mail.outbox)
        self.clickTagContaining("button", buttonText)
        self.assert_on_MembersOnly_SentEmail()
        self.assertEqual(len(mail.outbox), before_count+1)
        self.clickTagContaining("button", "OK")
        self.assert_on_CheckInDone()

        buttonText = "Pay Now at Front Desk"
        print("  "+buttonText)
        checkin()
        self.clickTagContaining("button", buttonText)
        self.assert_on_MembersOnly_PayNow()
        self.clickTagContaining("button", "OK")
        self.assert_on_CheckInDone()

        buttonText = "I'm Current!"
        print("  "+buttonText)
        checkin()
        self.clickTagContaining("button", buttonText)
        self.assert_on_CheckInDone()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_CheckMembershipPrivilegesLogic(self):
        print("Check Membership Privileges Logic")

        def checkin(dayOfMonth, hours, minutes, endcheck, msg):
            now = make_aware(datetime.now())
            pit = make_aware(datetime(2018, 2, dayOfMonth, hours, minutes, 00))
            time_shift = floor((pit - now).total_seconds())  # type: int
            with freeze_time(pit):
                print("  "+datetime.now().isoformat()+": "+msg)
                self.load_to_start(time_shift)
                self.start_to_welcome()
                self.welcome_to_checkIn()
                self.checkIn_to_reasonForVisit_viaFlexId(self.EXISTING_USERNAME, self.EXISTING_USERNAME)
                self.reasonForVisit_to_next_viaReason(self.REASON_MEMBER)
                endcheck()

        checkin(  # year=2018, month=2
            dayOfMonth=19, hours=20, minutes=00, endcheck=self.assert_on_MembersOnly,
            msg="During Monday members-only block, no membership ever. NOT allowed.")

        checkin(  # year=2018, month=2
            dayOfMonth=22, hours=12, minutes=00, endcheck=self.assert_on_MembersOnly,
            msg="Thursday, default block, no membership ever. NOT allowed.")

        checkin(  # year=2018, month=2
            dayOfMonth=22, hours=20, minutes=00, endcheck=self.assert_on_CheckInDone,
            msg="During Thursday open-house block, no membership ever. Allowed.")

        # Add an EXPIRED membership:

        Membership.objects.create(
            member=self.existing_member,
            start_date=date(2018, 1, 1),
            end_date=date(2018, 1, 2)
        )

        checkin(  # year=2018, month=2
            dayOfMonth=19, hours=20, minutes=00, endcheck=self.assert_on_MembersOnly,
            msg="During Monday members-only block, EXPIRED membership. NOT allowed.")

        checkin(  # year=2018, month=2
            dayOfMonth=22, hours=12, minutes=00, endcheck=self.assert_on_MembersOnly,
            msg="Thursday, default block, EXPIRED membership. NOT allowed.")

        checkin(  # year=2018, month=2
            dayOfMonth=22, hours=20, minutes=00, endcheck=self.assert_on_CheckInDone,
            msg="During Thursday open-house block, EXPIRED membership. Allowed.")

        # Add an FUTURE membership:

        Membership.objects.create(
            member=self.existing_member,
            start_date=date(2019, 1, 1),
            end_date=date(2019, 1, 2)
        )

        checkin(  # year=2018, month=2
            dayOfMonth=19, hours=20, minutes=00, endcheck=self.assert_on_MembersOnly,
            msg="During Monday members-only block, FUTURE membership. NOT allowed.")

        checkin(  # year=2018, month=2
            dayOfMonth=22, hours=12, minutes=00, endcheck=self.assert_on_MembersOnly,
            msg="Thursday, default block, FUTURE membership. NOT allowed.")

        checkin(  # year=2018, month=2
            dayOfMonth=22, hours=20, minutes=00, endcheck=self.assert_on_CheckInDone,
            msg="During Thursday open-house block, FUTURE membership. Allowed.")

        # Add an CURRENT membership:

        Membership.objects.create(
            member=self.existing_member,
            start_date=date(2018, 2, 1),
            end_date=date(2018, 3, 1)
        )

        checkin(  # year=2018, month=2
            dayOfMonth=19, hours=20, minutes=00, endcheck=self.assert_on_CheckInDone,
            msg="During Monday members-only block, CURRENT membership. Allowed.")

        checkin(  # year=2018, month=2
            dayOfMonth=22, hours=12, minutes=00, endcheck=self.assert_on_CheckInDone,
            msg="Thursday, default block, CURRENT membership. Allowed.")

        checkin(  # year=2018, month=2
            dayOfMonth=22, hours=20, minutes=00, endcheck=self.assert_on_CheckInDone,
            msg="During Thursday open-house block, CURRENT membership. Allowed.")

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_OtherTaskStartAndFinish(self):

        print("Other Work, Start & Finish")

        # Check IN and start work on task
        self.load_to_start()
        self.start_to_welcome()
        self.welcome_to_checkIn()
        self.checkIn_to_reasonForVisit_viaFlexId(self.EXISTING_USERNAME, self.EXISTING_USERNAME)
        self.reasonForVisit_to_next_viaReason(self.REASON_WORK)
        self.taskList_to_taskInfo_viaTaskName(self.OTHER_WORK_SHORT_DESC)
        self.taskInfo_to_checkInDone()
        self.checkInDone_to_start()

        # Verify state at this point:
        latestEvent = VisitEvent.objects.latest('when')
        self.assertEqual(latestEvent.event_type, VisitEvent.EVT_ARRIVAL)
        self.assertEqual(latestEvent.reason, VisitEvent.REASON_VOLUNTEER)
        self.assertEqual(Claim.objects.filter(status=Claim.STAT_WORKING).count(), 1)

        # Check OUT and close the old business
        self.start_to_welcome()
        self.welcome_to_checkOut()
        self.checkOut_to_next_viaUname(self.EXISTING_USERNAME)
        self.oldBusiness_to_timeSheetPt1_viaTaskName(self.OTHER_WORK_SHORT_DESC)
        self.timeSheetPt1_to_next()  # In this case, it'll go to Pt2
        self.timeSheetPt2_to_timeSheetPt3_viaDesc(self.LONG_TEXT)
        # Test that back button visits Pt2 scene for this "Other Work" case.
        self.backOneScene()
        self.timeSheetPt2_to_timeSheetPt3_viaDesc("")
        # End of back button subtest.
        self.timeSheetPt3_to_next_viaIdPw(self.WITNESS_USERNAME, self.WITNESS_PASSWORD)
        # In this case, above line will take us to CheckOutDone
        self.checkOutDone_to_start()

        self.assertEqual(Claim.objects.filter(status=Claim.STAT_WORKING).count(), 0)
        self.assertEqual(TimeAccountEntry.objects.count(), 1)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_StartAndSkipAndFinish(self):

        print("Specific Task, Start & Skip & Finish")
        self.assertEqual(Claim.objects.filter(status=Claim.STAT_WORKING).count(), 0)

        # Check IN and claim a task
        self.load_to_start()
        self.start_to_welcome()
        self.welcome_to_checkIn()
        self.checkIn_to_reasonForVisit_viaFlexId(self.EXISTING_USERNAME, self.EXISTING_USERNAME)
        self.reasonForVisit_to_next_viaReason(self.REASON_WORK)
        self.taskList_to_taskInfo_viaDefault()
        self.taskInfo_to_checkInDone()
        self.checkInDone_to_start()

        # Verify state at this point:
        latestEvent = VisitEvent.objects.latest('when')
        self.assertEqual(latestEvent.event_type, VisitEvent.EVT_ARRIVAL)
        self.assertEqual(latestEvent.reason, VisitEvent.REASON_VOLUNTEER)
        self.assertEqual(Claim.objects.filter(status=Claim.STAT_WORKING).count(), 1)

        # Check OUT and skip the old business
        self.start_to_welcome()
        self.welcome_to_checkOut()
        self.checkOut_to_next_viaUname(self.EXISTING_USERNAME)
        self.oldBusiness_to_next_viaSkip()
        self.checkOutDone_to_start()

        # Verify state at this point:
        latestEvent = VisitEvent.objects.latest('when')
        self.assertEqual(latestEvent.event_type, VisitEvent.EVT_DEPARTURE)
        self.assertEqual(latestEvent.reason, None)
        self.assertEqual(Claim.objects.filter(status=Claim.STAT_WORKING).count(), 1)

        # Check IN and finish the task
        self.start_to_welcome()
        self.welcome_to_checkIn()
        self.checkIn_to_reasonForVisit_viaFlexId(self.EXISTING_USERNAME, self.EXISTING_USERNAME)
        self.reasonForVisit_to_next_viaReason(self.REASON_OTHER)
        self.oldBusiness_to_timeSheetPt1_viaTaskName(self.SPECIFIC_TASK_SHORT_DESC)
        self.timeSheetPt1_to_next()  # In this case, it'll go to Pt3
        self.timeSheetPt3_to_next_viaIdPw(self.WITNESS_USERNAME, self.WITNESS_PASSWORD)
        # In this case, above line will take us to CheckInDone
        self.checkInDone_to_start()

        # Verify state at this point:
        latestEvent = VisitEvent.objects.filter(who=self.existing_member).latest('when')
        self.assertEqual(latestEvent.event_type, VisitEvent.EVT_ARRIVAL)
        self.assertEqual(latestEvent.reason, VisitEvent.REASON_OTHER)
        # TODO: There's no "present" event if witness doesn't use RFID, but there should be:
        # latestEvent = VisitEvent.objects.filter(who=self.witness_member).latest('when')
        # self.assertEqual(latestEvent.event_type, VisitEvent.EVT_PRESENT)

        self.assertEqual(Claim.objects.filter(status=Claim.STAT_WORKING).count(), 0)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_SimpleTaskStartAndDelete(self):
        print("Specific Task, Start and Delete")
        self.assertEqual(Claim.objects.filter(status=Claim.STAT_WORKING).count(), 0)

        # Check in and claim a task
        self.load_to_start()
        self.start_to_welcome()
        self.welcome_to_checkIn()
        self.checkIn_to_reasonForVisit_viaFlexId(self.EXISTING_USERNAME, self.EXISTING_USERNAME)
        self.reasonForVisit_to_next_viaReason(self.REASON_WORK)
        self.taskList_to_taskInfo_viaDefault()
        self.taskInfo_to_checkInDone()
        self.checkInDone_to_start()

        self.assertTrue(VisitEvent.objects.all().count() >= 1)
        self.assertEqual(Claim.objects.filter(status=Claim.STAT_WORKING).count(), 1)

        # Check out and delete the claim
        self.start_to_welcome()
        self.welcome_to_checkOut()
        self.checkOut_to_next_viaUname(self.EXISTING_USERNAME)
        self.oldBusiness_to_next_viaDelete(self.SPECIFIC_TASK_SHORT_DESC)
        self.checkOutDone_to_start()

        self.assertEqual(Claim.objects.filter(status=Claim.STAT_WORKING).count(), 0)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_CheckInAndOutUsingKeyboard(self):
        print("Simple Check In & Check Out")

        # Check in using userid
        self.load_to_start()
        self.start_to_welcome()
        self.welcome_to_checkIn()
        self.checkIn_to_reasonForVisit_viaFlexId(self.EXISTING_USERNAME, self.EXISTING_USERNAME)
        self.reasonForVisit_to_next_viaReason(self.REASON_OTHER)
        self.checkInDone_to_start()

        # Check in using last name
        self.start_to_welcome()
        self.welcome_to_checkIn()
        self.checkIn_to_reasonForVisit_viaFlexId(self.existing_member.last_name, self.EXISTING_USERNAME)
        self.reasonForVisit_to_next_viaReason(self.REASON_OTHER)
        self.checkInDone_to_start()

        # Check out
        self.start_to_welcome()
        self.welcome_to_checkOut()
        self.checkOut_to_next_viaUname(self.EXISTING_USERNAME)
        self.checkOutDone_to_start()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def test_AllSimpleCheckIns(self):
        print("All Simple Check Ins")
        self.load_to_start()
        for reason in self.simple_reasons:
            print("  "+reason)
            self.start_to_welcome()
            self.welcome_to_checkIn()
            self.checkIn_to_reasonForVisit_viaFlexId(self.EXISTING_USERNAME, self.EXISTING_USERNAME)
            self.reasonForVisit_to_next_viaReason(reason)
            self.checkInDone_to_start()
