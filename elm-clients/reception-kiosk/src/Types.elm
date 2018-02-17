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

-----------------------------------------------------------------------------
-- FLAGS
-----------------------------------------------------------------------------

-- This type can move into ReceiptionKiosk.elm, but for the banner fields.
type alias Flags =
  { bannerBottomUrl : String
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
  | HowDidYouHear
  | SignUpDone
  | MembersOnly
  | NewMember
  | NewUser
  | OldBusiness
  | ReasonForVisit
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
    HowDidYouHear -> 700
    MembersOnly -> 800
    NewMember -> 900
    NewUser -> 1000
    OldBusiness -> 1100
    ReasonForVisit -> 1200
    ScreenSaver -> 1300
    SignUpDone -> 1400
    TaskInfo -> 1500
    TaskList -> 1600
    TimeSheetPt1 -> 1700
    TimeSheetPt2 -> 1800
    TimeSheetPt3 -> 1900
    Waiver -> 2000
    Welcome -> 2100
    WelcomeForRfid -> 2200


-----------------------------------------------------------------------------
-- MSG TYPES
-----------------------------------------------------------------------------

type CheckInMsg
  = UsernamesStartingWith String (Result Http.Error (PageOf Member))
  | UsernamesEqualTo String (Result Http.Error (PageOf Member))
  | LastNamesStartingWith String (Result Http.Error (PageOf Member))
  | LastNamesEqualTo String (Result Http.Error (PageOf Member))
  | UpdateRecentRfidsRead (Result Http.Error (PageOf VisitEvent))
  | CI_UpdateFlexId String
  | CI_UpdateMember (Result String Member)

type CheckOutMsg
  = AccVisitEvents (Result Http.Error (PageOf VisitEvent))
  | LogCheckOut Int
  | LogCheckOutResult (Result Http.Error VisitEvent)

type CreatingAcctMsg
  = XcAcctCreationAttempted (Result Http.Error String)
  | CloneAttempted (Result Http.Error String)
  | IsAdultWasSet (Result Http.Error String)
  | DiscoveryMethodAdded (Result Http.Error String)

type HowDidYouHearMsg
  = AccDiscoveryMethods (Result Http.Error (PageOf DiscoveryMethod))  -- "Acc" means "accumulate"
  | ToggleDiscoveryMethod DiscoveryMethod
  | ShuffledDiscoveryMethods (List DiscoveryMethod)

type MembersOnlyMsg
  = UpdateTimeBlocks (Result Http.Error (PageOf TimeBlock))
  | UpdateTimeBlockTypes (Result Http.Error (PageOf TimeBlockType))
  | PayNowAtFrontDesk
  | SendPaymentInfo

type NewMemberMsg
  = UpdateFirstName String
  | UpdateLastName String
  | UpdateEmail String
  | ToggleIsAdult Bool
  | Validate
  | ValidateEmailUnique (Result Http.Error MatchingAcctInfo)

type NewUserMsg
  = ValidateUserNameAndPw
  | ValidateUserNameUnique (Result Http.Error MatchingAcctInfo)
  | UpdateUserName String
  | UpdatePassword1 String
  | UpdatePassword2 String

type OldBusinessMsg
  = OB_WorkingClaimsResult (Result Http.Error (PageOf Claim))
  | OB_DeleteSelection
  | OB_NoteRelatedTask Claim (Result Http.Error XisApi.Task)
  | OB_NoteRelatedWork XisApi.Task Claim (Result Http.Error Work)
  | OB_ToggleItem Int
  | OB_NoteWorkDeleted (Result Http.Error String)
  | OB_NoteClaimUpdated (Result Http.Error Claim)

type ReasonForVisitMsg
  = UpdateReasonForVisit VisitEventReason
  | ValidateReason
  | LogCheckInResult (Result Http.Error VisitEvent)

type RfidHelperMsg
  = RH_KeyDown KeyCode
  | RH_MemberListResult (Result Http.Error (PageOf Member))
  | RH_MemberPresentResult (Result Http.Error VisitEvent)

type ScreenSaverMsg
  = SS_KeyDown KeyCode
  | SS_MouseClick

type TaskListMsg
  = TL_TaskListResult (Result Http.Error (PageOf XisApi.Task))
  | TL_ToggleTask XisApi.Task
  | TL_ValidateTaskChoice
  | TL_ClaimUpsertResult (Result Http.Error Claim)
  | TL_WorkInsertResult (Result Http.Error Work)

type TimeSheetPt1Msg
  = TS1_Submit XisApi.Task Claim Work
  | TS1_HrPad Int
  | TS1_MinPad Int

type TimeSheetPt2Msg
  = TS2_UpdateDescription String
  | TS2_Continue

type TimeSheetPt3Msg
  = TS3_UpdateWitnessUsername String
  | TS3_UpdateWitnessPassword String
  | TS3_Witnessed
  | TS3_Skipped
  | TS3_NeedWitness
  | TS3_ClaimUpdated (Result Http.Error Claim)
  | TS3_WorkUpdated (Result Http.Error Work)
  | TS3_WorkNoteCreated (Result Http.Error WorkNote)
  | TS3_WitnessAuthResult (Result Http.Error AuthenticationResult)

type WaiverMsg
  = ShowSignaturePad String
  | ClearSignaturePad String
  | GetSignature
  | UpdateSignature String  -- String is a data URL representation of an image.

type Msg
  = MdlVector (Material.Msg Msg)
  | WizardVector WizardMsg
  | RfidHelperVector RfidHelperMsg
  | RfidWasSwiped (Result String Member)
  -----------------------------------
  | CheckInVector CheckInMsg
  | CheckOutVector CheckOutMsg
  | CreatingAcctVector CreatingAcctMsg
  | HowDidYouHearVector HowDidYouHearMsg
  | MembersOnlyVector MembersOnlyMsg
  | NewMemberVector NewMemberMsg
  | NewUserVector NewUserMsg
  | OldBusinessVector OldBusinessMsg
  | ReasonForVisitVector ReasonForVisitMsg
  | ScreenSaverVector ScreenSaverMsg
  | TaskListVector TaskListMsg
  | TimeSheetPt1Vector TimeSheetPt1Msg
  | TimeSheetPt2Vector TimeSheetPt2Msg
  | TimeSheetPt3Vector TimeSheetPt3Msg
  | WaiverVector WaiverMsg

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

