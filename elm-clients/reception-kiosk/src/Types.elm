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
    VolunteerInDone -> 1500
    Waiver -> 1600
    Welcome -> 1700


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
  = TaskListResult (Result Http.Error (PageOf XisApi.Task))
  | ToggleTask XisApi.Task
  | ValidateTaskChoice

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
  | WaiverVector WaiverMsg

type WizardMsg
  = Push Scene
  | RebaseTo Scene
  | Pop
  | Reset
  | SceneWillAppear Scene
  | Tick Time
