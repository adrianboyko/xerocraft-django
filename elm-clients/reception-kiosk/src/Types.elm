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
import MembersApi exposing (..)
import TaskApi exposing (..)
import XisRestApi as XisApi exposing (..)

-----------------------------------------------------------------------------
-- FLAGS
-----------------------------------------------------------------------------

-- This type can move into ReceiptionKiosk.elm, but for the banner fields.
type alias Flags =
  { addDiscoveryMethodUrl : String
  , bannerBottomUrl : String
  , bannerTopUrl : String
  , checkedInAcctsUrl : String
  , claimListUrl : String
  , cloneAcctUrl : String
  , csrfToken : String
  , discoveryMethodsUrl : String
  , logVisitEventUrl : String
  , matchingAcctsUrl : String
  , memberListUrl : String
  , membershipListUrl : String
  , orgName : String
  , recentRfidEntriesUrl : String
  , scrapeLoginsUrl : String
  , setIsAdultUrl : String
  , taskListUrl : String
  , timeBlocksUrl : String
  , timeBlockTypesUrl : String
  , uniqueKioskId : String
  , wavingHandUrl : String
  , workListUrl : String
  , workNoteListUrl : String
  , xcOrgActionUrl : String
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
  | ReasonForVisit
  | ScreenSaver
  | TaskList
  | TimeSheetPt1
  | TimeSheetPt2
  | TimeSheetPt3
  | VolunteerInDone
  | Waiver
  | Welcome

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
    ReasonForVisit -> 1100
    ScreenSaver -> 1200
    SignUpDone -> 1300
    TaskList -> 1400
    TimeSheetPt1 -> 1500
    TimeSheetPt2 -> 1600
    TimeSheetPt3 -> 1700
    VolunteerInDone -> 1800
    Waiver -> 1900
    Welcome -> 2000


-----------------------------------------------------------------------------
-- MSG TYPES
-----------------------------------------------------------------------------

type CheckInMsg
  = UpdateMatchingAccts (Result Http.Error MatchingAcctInfo)
  | UpdateFlexId String
  | UpdateMemberNum Int
  | FlexIdFocusSet Bool
  | CheckInShortcut String Int -- Allows RFID reading scene to short-cut through this scene

type CheckOutMsg
  = UpdateCheckedInAccts (Result Http.Error MatchingAcctInfo)
  | LogCheckOut Int
  | LogCheckOutResult (Result Http.Error GenericResult)

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
  = UpdateMemberships (Result Http.Error (PageOf Membership))
  | UpdateTimeBlocks (Result Http.Error (PageOf TimeBlock))
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
  | FirstNameFocusSet Bool

type NewUserMsg
  = ValidateUserNameAndPw
  | ValidateUserNameUnique (Result Http.Error MatchingAcctInfo)
  | UpdateUserName String
  | UpdatePassword1 String
  | UpdatePassword2 String
  | UserNameFocusSet Bool

type ReasonForVisitMsg
  = UpdateReasonForVisit ReasonForVisit
  | ValidateReason
  | LogCheckInResult (Result Http.Error GenericResult)

type ScreenSaverMsg
  = SS_KeyDown KeyCode
  | SS_MouseClick
  | SS_MemberListResult (Result Http.Error (PageOf XisApi.Member))

type TaskListMsg
  = TL_TaskListResult (Result Http.Error (PageOf XisApi.Task))
  | TL_ToggleTask XisApi.Task
  | TL_ValidateTaskChoice
  | TL_ClaimUpsertResult (Result Http.Error XisApi.Claim)
  | TL_WorkInsertResult (Result Http.Error XisApi.Work)

type TimeSheetPt1Msg
  = TS1_WorkingClaimsResult (Result Http.Error (PageOf XisApi.Claim))
  | TS1_WorkingTaskResult (Result Http.Error XisApi.Task)
  | TS1_WipResult (Result Http.Error (PageOf XisApi.Work))
  | TS1_Submit XisApi.Claim XisApi.Work
  | TS1_UpdateDuration String
  | TS1_UpdateTimeStarted String

type TimeSheetPt2Msg
  = TS2_UpdateDescription String
  | TS2_Continue

type TimeSheetPt3Msg
  = TS3_UpdateWitnessUsername String
  | TS3_UpdateWitnessPassword String
  | TS3_Witnessed
  | TS3_WitnessSearchResult (Result Http.Error (PageOf XisApi.Member))
  | TS3_ClaimUpdated (Result Http.Error XisApi.Claim)
  | TS3_WorkUpdated (Result Http.Error XisApi.Work)
  | TS3_WorkNoteCreated (Result Http.Error XisApi.WorkNote)

type WaiverMsg
  = ShowSignaturePad String
  | ClearSignaturePad String
  | GetSignature
  | UpdateSignature String  -- String is a data URL representation of an image.

type Msg
  = MdlVector (Material.Msg Msg)
  | WizardVector WizardMsg
  | CheckInVector CheckInMsg
  | CheckOutVector CheckOutMsg
  | CreatingAcctVector CreatingAcctMsg
  | HowDidYouHearVector HowDidYouHearMsg
  | MembersOnlyVector MembersOnlyMsg
  | NewMemberVector NewMemberMsg
  | NewUserVector NewUserMsg
  | ReasonForVisitVector ReasonForVisitMsg
  | ScreenSaverVector ScreenSaverMsg
  | TaskListVector TaskListMsg
  | TimeSheetPt1Vector TimeSheetPt1Msg
  | TimeSheetPt2Vector TimeSheetPt2Msg
  | TimeSheetPt3Vector TimeSheetPt3Msg
  | WaiverVector WaiverMsg

type WizardMsg
  = Push Scene
  | RebaseTo Scene
  | Pop
  | Reset
  | SceneWillAppear Scene Scene  -- Appearing scene, Vanishing scene
  | Tick Time
