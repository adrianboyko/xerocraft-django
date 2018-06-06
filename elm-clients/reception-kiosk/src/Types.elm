module Types exposing (..)

-- Standard
import Http
import Time exposing (Time)
import Keyboard exposing (KeyCode)
import Mouse exposing (Position)

-- Third Party
import Material
import List.Nonempty exposing (Nonempty)

-- Local
import DjangoRestFramework exposing (PageOf)
import MembersApi as MembersApi exposing (..)
import XisRestApi as XisApi exposing
  ( AuthenticationResult
  , Claim
  , DiscoveryMethod
  , Member
  , Play
  , TimeBlock
  , TimeBlockType
  , VisitEvent
  , VisitEventReason
  , Work
  , WorkNote
  , XisRestFlags
  )
import Duration exposing (Duration)


-----------------------------------------------------------------------------
-- GLOBAL CONSTANTS
-----------------------------------------------------------------------------

missingArguments = "Can't continue because required arguments were not received."

-----------------------------------------------------------------------------
-- FLAGS
-----------------------------------------------------------------------------

-- This type can move into ReceiptionKiosk.elm, but for the banner fields.
type alias Flags =
  { timeShift : Duration
  , bannerBottomUrl : String
  , bannerTopUrl : String
  , cloneAcctUrl : String
  , csrfToken : String
  , membersApiFlags : MembersApi.Flags
  , orgName : String
  , scrapeLoginsUrl : String
  , uniqueKioskId : String
  , wavingHandUrl : String
  , xcOrgActionUrl : String
  , xisApiFlags : XisRestFlags
  }

-----------------------------------------------------------------------------
-- SCENES
-----------------------------------------------------------------------------

type Scene
  = AuthorizeEntry
  | BuyMembership
  | CheckIn
  | CheckInDone
  | CheckOut
  | CheckOutDone
  | CreatingAcct
  | DispenseSoda
  | EmailInUse
  | Error
  | HowDidYouHear
  | NewMember
  | NewUser
  | OldBusiness
  | PublicHours
  | ReasonForVisit
  | RfidHelper  -- The view for RfidHelper is an error message.
  | SignUpDone
  | Start
  | TaskInfo
  | TaskList
  | TimeSheetPt1
  | TimeSheetPt2
  | TimeSheetPt3
  | UseBankedHours
  | Waiver
  | Welcome
  | WelcomeForRfid
  | YouCantEnter

-- Material id space needs to be chopped up for scenes:
mdlIdBase : Scene -> Int
mdlIdBase scene =
  case scene of
    AuthorizeEntry -> 900
    BuyMembership -> 2500
    CheckIn -> 100
    CheckInDone -> 200
    CheckOut -> 300
    CheckOutDone -> 400
    CreatingAcct -> 500
    DispenseSoda -> 2900  -- Current Max
    EmailInUse -> 600
    Error -> 700
    HowDidYouHear -> 800
    NewMember -> 1000
    NewUser -> 1100
    OldBusiness -> 1200
    PublicHours -> 2800
    ReasonForVisit -> 1300
    RfidHelper -> 2400
    SignUpDone -> 1500
    Start -> 1400
    TaskInfo -> 1600
    TaskList -> 1700
    TimeSheetPt1 -> 1800
    TimeSheetPt2 -> 1900
    TimeSheetPt3 -> 2000
    UseBankedHours -> 2600
    Waiver -> 2100
    Welcome -> 2200
    WelcomeForRfid -> 2300
    YouCantEnter -> 2700

-----------------------------------------------------------------------------
-- KIOSK SESSIION TYPE
-----------------------------------------------------------------------------

type SessionType = CheckInSession | CheckOutSession

sessionTypeStr st =
  case st of
    CheckInSession -> "check in"
    CheckOutSession -> "check out"

-----------------------------------------------------------------------------
-- MSG TYPES
-----------------------------------------------------------------------------

type alias TaskClaimWork =
  { task: XisApi.Task
  , claim: XisApi.Claim
  , work: XisApi.Work  -- If they're not working it, it's not old/unfinished business.
  }

-----------------------------------------------------------------------------
-- MSG TYPES
-----------------------------------------------------------------------------

type BuyMembershipMsg
  = BM_Segue Member

type CheckInDoneMsg
  = CID_Segue Member

type CheckInMsg
  = UsernamesStartingWith String (Result Http.Error (PageOf Member))
  | UsernamesEqualTo String (Result Http.Error (PageOf Member))
  | LastNamesStartingWith String (Result Http.Error (PageOf Member))
  | LastNamesEqualTo String (Result Http.Error (PageOf Member))
  | UpdateRecentRfidsRead (Result Http.Error (PageOf VisitEvent))
  | CI_UpdateFlexId String
  | CI_UpdateMember (Result String Member)

type CheckOutDoneMsg
  = COD_Segue Member
  | COD_LogCheckOutResult (Result Http.Error VisitEvent)

type CheckOutMsg
  = CO_AccVisitEvents (Result Http.Error (PageOf VisitEvent))
  | CO_MemberChosen Member

type CreatingAcctMsg
  = CA_Segue (List Int, String, String, String, Bool, String, String, String)
  | XcAcctCreationAttempted (Result Http.Error String)
  | CloneAttempted (Result Http.Error String)
  | IsAdultWasSet (Result Http.Error String)
  | DiscoveryMethodAdded (Result Http.Error String)

type DispenseSodaMsg
  = DS_Segue Member
  | DS_Dispense Member Int

type ErrorMsg
  = ERR_Segue String
  | ERR_ResetClicked

type EmailInUseMsg
  = EIU_Segue (List Member)

type HowDidYouHearMsg
  = AccDiscoveryMethods (Result Http.Error (PageOf DiscoveryMethod))  -- "Acc" means "accumulate"
  | ToggleDiscoveryMethod DiscoveryMethod
  | ShuffledDiscoveryMethods (List DiscoveryMethod)
  | OkClicked

type AuthorizeEntryMsg
  = AE_Segue Member (Maybe TimeBlock) (List TimeBlockType)

type NewMemberMsg
  = NM_Segue (List Int)  -- DiscoveryMethod PKs
  | UpdateFirstName String
  | UpdateLastName String
  | UpdateEmail String
  | ToggleIsAdult Bool
  | Validate
  | ValidateEmailUnique (Result Http.Error (PageOf Member))

type NewUserMsg
  = NU_Segue (List Int, String, String, String, Bool)
  | ValidateUserNameAndPw
  | ValidateUserNameUnique (Result Http.Error (PageOf Member))
  | UpdateUserName String
  | UpdatePassword1 String
  | UpdatePassword2 String

type Business
  = SomeTCW TaskClaimWork
  | SomePlay Play

type OldBusinessMsg
  = OB_SegueA SessionType Member
  | OB_SegueB SessionType Member Business
  | OB_WorkingClaimsResult (Result Http.Error (PageOf Claim))
  | OB_OpenPlaysResult (Result Http.Error (PageOf Play))
  | OB_DeleteSelection
  | OB_NoteRelatedTask Claim (Result Http.Error XisApi.Task)
  | OB_NoteRelatedWork XisApi.Task Claim (Result Http.Error Work)
  | OB_NotePlayDeleted (Result Http.Error String)
  | OB_ToggleItem Business
  | OB_NoteWorkDeleted (Result Http.Error String)
  | OB_NoteClaimUpdated (Result Http.Error Claim)

type PublicHoursMsg
  = PH_Segue Member

type ReasonForVisitMsg
  = R4V_Segue Member
  | UpdateTimeBlocks (Result Http.Error (PageOf TimeBlock))
  | UpdateTimeBlockTypes (Result Http.Error (PageOf TimeBlockType))
  | UpdateReasonForVisit VisitEventReason
  | ValidateReason
  | LogCheckInResult (Result Http.Error VisitEvent)

type RfidHelperMsg
  = RH_KeyDown KeyCode
  | RH_MemberListResult (Result Http.Error (PageOf Member))
  | RH_MemberPresentResult (Result Http.Error VisitEvent)

type SignUpDoneMsg
  = SUD_Segue String

type StartMsg
  = SS_KeyDown KeyCode
  | SS_MouseClick Position

type TaskInfoMsg
  = TI_Segue Member TaskClaimWork

type TaskListMsg
  = TL_Segue Member
  | TL_TaskListResult (Result Http.Error (PageOf XisApi.Task))
  | TL_ToggleTask XisApi.Task
  | TL_ValidateTaskChoice
  | TL_ClaimUpsertResult (Result Http.Error Claim)
  | TL_WorkInsertResult (Result Http.Error Work)

type TimeSheetPt1Msg
  = TS1_Segue SessionType Member Business
  | TS1_Submit SessionType Member Business
  | TS1_HrPad Int
  | TS1_MinPad Int
  | TS1_ReplacePlay_Result (Result Http.Error Play)

type TimeSheetPt2Msg
  = TS2_Segue SessionType Member TaskClaimWork
  | TS2_UpdateDescription String
  | TS2_Continue

type TimeSheetPt3Msg
  = TS3_Segue SessionType Member TaskClaimWork (Maybe String)
  | TS3_UpdateWitnessUsername String
  | TS3_UpdateWitnessPassword String
  | TS3_WitnessCredsReady
  | TS3_Skipped
  | TS3_NeedWitness
  | TS3_ClaimUpdated (Result Http.Error Claim)
  | TS3_WorkUpdated (Result Http.Error Work)
  | TS3_WorkNoteCreated (Result Http.Error WorkNote)
  | TS3_WitnessAuthResult (Result Http.Error AuthenticationResult)

type UseBankedHoursMsg
  = UBH_Segue Member
  | UseSomeHours_Clicked Member
  | WillVolunteer_Clicked Member
  | PlayCreation_Result Member (Result Http.Error Play)
  | PlayList_Result Member (Result Http.Error (PageOf Play))

type WaiverMsg
  = WVR_Segue (List Int, String, String, String, Bool, String, String)
  | ShowSignaturePad String
  | ClearSignaturePad String
  | GetSignature
  | UpdateSignature String  -- String is a data URL representation of an image.

type WelcomeForRfidMsg
  = W4R_Segue Member
  | W4R_CheckInClicked
  | W4R_CheckOutClicked

type YouCantEnterMsg
  = YCE_Segue Member
  | PayNowAtFrontDesk_Clicked Member
  | AlreadyPaid_Clicked Member
  | UseBankedHours_Clicked Member


type Msg
  = MdlVector (Material.Msg Msg)
  | WizardVector WizardMsg
  | RfidHelperVector RfidHelperMsg
  | RfidWasSwiped (Result String Member)
  | NoOp
  | IgnoreResultHttpErrorString (Result Http.Error String)
  -----------------------------------
  | AuthorizeEntryVector AuthorizeEntryMsg
  | BuyMembershipVector BuyMembershipMsg
  | CheckInDoneVector CheckInDoneMsg
  | CheckInVector CheckInMsg
  | CheckOutDoneVector CheckOutDoneMsg
  | CheckOutVector CheckOutMsg
  | CreatingAcctVector CreatingAcctMsg
  | DispenseSodaVector DispenseSodaMsg
  | EmailInUseVector EmailInUseMsg
  | ErrorVector ErrorMsg
  | HowDidYouHearVector HowDidYouHearMsg
  | NewMemberVector NewMemberMsg
  | NewUserVector NewUserMsg
  | OldBusinessVector OldBusinessMsg
  | PublicHoursVector PublicHoursMsg
  | ReasonForVisitVector ReasonForVisitMsg
  | SignUpDoneVector SignUpDoneMsg
  | StartVector StartMsg
  | TaskInfoVector TaskInfoMsg
  | TaskListVector TaskListMsg
  | TimeSheetPt1Vector TimeSheetPt1Msg
  | TimeSheetPt2Vector TimeSheetPt2Msg
  | TimeSheetPt3Vector TimeSheetPt3Msg
  | UseBankedHoursVector UseBankedHoursMsg
  | WaiverVector WaiverMsg
  | WelcomeForRfidVector WelcomeForRfidMsg
  | YouCantEnterVector YouCantEnterMsg

type WizardMsg
  = Push Scene
  | Rebase  -- Removes everything on stack under top scene.
  | RebaseTo Scene  -- Like Rebase but only removes scenes under top scene down to specified scene (exclusive).
  | Pop
  | PopTo Scene -- Removes everything on the stack above the specified scene.
  | ReplaceWith Scene  -- REPLACES the current top.
  | Reset
  | SceneWillAppear Scene Scene  -- Appearing scene, Vanishing scene
  | Tick Time
  | FocusWasSet Bool
  | FocusOnIndex (List Int) -- Can't use Material.Component.Index (https://github.com/debois/elm-mdl/issues/342)

