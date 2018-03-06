module Types exposing (..)

-- Standard
import Http
import Time exposing (Time)
import Keyboard exposing (KeyCode)

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
  = CheckIn
  | CheckInDone
  | CheckOut
  | CheckOutDone
  | CreatingAcct
  | EmailInUse
  | Error
  | HowDidYouHear
  | SignUpDone
  | MembersOnly
  | NewMember
  | NewUser
  | OldBusiness
  | ReasonForVisit
  | RfidHelper  -- The view for RfidHelper is an error message.
  | ScreenSaver
  | TaskList
  | TimeSheetPt1
  | TimeSheetPt2
  | TimeSheetPt3
  | TaskInfo
  | Waiver
  | Welcome
  | WelcomeForRfid

-- Material id space needs to be chopped up for scenes:
mdlIdBase : Scene -> Int
mdlIdBase scene =
  case scene of
    CheckIn -> 100
    CheckInDone -> 200
    CheckOut -> 300
    CheckOutDone -> 400
    CreatingAcct -> 500
    EmailInUse -> 600
    Error -> 700
    HowDidYouHear -> 800
    MembersOnly -> 900
    NewMember -> 1000
    NewUser -> 1100
    OldBusiness -> 1200
    ReasonForVisit -> 1300
    RfidHelper -> 2400  -- CURRENT MAX
    ScreenSaver -> 1400
    SignUpDone -> 1500
    TaskInfo -> 1600
    TaskList -> 1700
    TimeSheetPt1 -> 1800
    TimeSheetPt2 -> 1900
    TimeSheetPt3 -> 2000
    Waiver -> 2100
    Welcome -> 2200
    WelcomeForRfid -> 2300

-----------------------------------------------------------------------------
-- KIOSK SESSIION TYPE
-----------------------------------------------------------------------------

type SessionType = CheckInSession | CheckOutSession

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

type MembersOnlyMsg
  = MO_Segue Member
  | UpdateTimeBlocks (Result Http.Error (PageOf TimeBlock))
  | UpdateTimeBlockTypes (Result Http.Error (PageOf TimeBlockType))
  | PayNowAtFrontDesk
  | SendPaymentInfo
  | ServerSentPaymentInfo (Result Http.Error String)

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

type OldBusinessMsg
  = OB_SegueA (SessionType, Member)
  | OB_SegueB (SessionType, Member, Claim)
  | OB_WorkingClaimsResult (Result Http.Error (PageOf Claim))
  | OB_DeleteSelection
  | OB_NoteRelatedTask Claim (Result Http.Error XisApi.Task)
  | OB_NoteRelatedWork XisApi.Task Claim (Result Http.Error Work)
  | OB_ToggleItem Int
  | OB_NoteWorkDeleted (Result Http.Error String)
  | OB_NoteClaimUpdated (Result Http.Error Claim)

type ReasonForVisitMsg
  = R4V_Segue Member
  | UpdateReasonForVisit VisitEventReason
  | ValidateReason
  | LogCheckInResult (Result Http.Error VisitEvent)

type RfidHelperMsg
  = RH_KeyDown KeyCode
  | RH_MemberListResult (Result Http.Error (PageOf Member))
  | RH_MemberPresentResult (Result Http.Error VisitEvent)

type ScreenSaverMsg
  = SS_KeyDown KeyCode
  | SS_MouseClick

type SignUpDoneMsg
  = SUD_Segue String

type TaskInfoMsg
  = TI_Segue (Member, XisApi.Task, Claim)

type TaskListMsg
  = TL_Segue Member
  | TL_TaskListResult (Result Http.Error (PageOf XisApi.Task))
  | TL_ToggleTask XisApi.Task
  | TL_ValidateTaskChoice
  | TL_ClaimUpsertResult (Result Http.Error Claim)
  | TL_WorkInsertResult (Result Http.Error Work)

type TimeSheetPt1Msg
  = TS1_Segue TaskClaimWork
  | TS1_Submit XisApi.Task Claim Work
  | TS1_HrPad Int
  | TS1_MinPad Int

type TimeSheetPt2Msg
  = TS2_Segue TaskClaimWork
  | TS2_UpdateDescription String
  | TS2_Continue

type TimeSheetPt3Msg
  = TS3_Segue (TaskClaimWork, Maybe String)
  | TS3_UpdateWitnessUsername String
  | TS3_UpdateWitnessPassword String
  | TS3_Witnessed
  | TS3_Skipped
  | TS3_NeedWitness
  | TS3_ClaimUpdated (Result Http.Error Claim)
  | TS3_WorkUpdated (Result Http.Error Work)
  | TS3_WorkNoteCreated (Result Http.Error WorkNote)
  | TS3_WitnessAuthResult (Result Http.Error AuthenticationResult)

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

type Msg
  = MdlVector (Material.Msg Msg)
  | WizardVector WizardMsg
  | RfidHelperVector RfidHelperMsg
  | RfidWasSwiped (Result String Member)
  | NoOp
  -----------------------------------
  | CheckInDoneVector CheckInDoneMsg
  | CheckInVector CheckInMsg
  | CheckOutDoneVector CheckOutDoneMsg
  | CheckOutVector CheckOutMsg
  | CreatingAcctVector CreatingAcctMsg
  | EmailInUseVector EmailInUseMsg
  | ErrorVector ErrorMsg
  | HowDidYouHearVector HowDidYouHearMsg
  | MembersOnlyVector MembersOnlyMsg
  | NewMemberVector NewMemberMsg
  | NewUserVector NewUserMsg
  | OldBusinessVector OldBusinessMsg
  | ReasonForVisitVector ReasonForVisitMsg
  | ScreenSaverVector ScreenSaverMsg
  | SignUpDoneVector SignUpDoneMsg
  | TaskInfoVector TaskInfoMsg
  | TaskListVector TaskListMsg
  | TimeSheetPt1Vector TimeSheetPt1Msg
  | TimeSheetPt2Vector TimeSheetPt2Msg
  | TimeSheetPt3Vector TimeSheetPt3Msg
  | WaiverVector WaiverMsg
  | WelcomeForRfidVector WelcomeForRfidMsg

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

