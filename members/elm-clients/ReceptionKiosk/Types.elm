module ReceptionKiosk.Types exposing (..)

-- Standard
import Http
import Time exposing (Time)

-- Third Party
import Material
import List.Nonempty exposing (Nonempty)

-- Local
import MembersApi exposing (..)
import TaskApi exposing (..)

-----------------------------------------------------------------------------
-- FLAGS
-----------------------------------------------------------------------------

-- This type can move into ReceiptionKiosk.elm, but for the banner fields.
type alias Flags =
  { addDiscoveryMethodUrl : String
  , bannerBottomUrl : String
  , bannerTopUrl : String
  , checkedInAcctsUrl : String
  , cloneAcctUrl : String
  , csrfToken : String
  , discoveryMethodsUrl : String
  , logVisitEventUrl : String
  , matchingAcctsUrl : String
  , orgName : String
  , scrapeLoginsUrl : String
  , setIsAdultUrl : String
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
  | NewMember
  | NewUser
  | ReasonForVisit
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
    SignUpDone -> 800
    NewMember -> 900
    NewUser -> 1000
    ReasonForVisit -> 1100
    TaskList -> 1200
    VolunteerInDone -> 1300
    Waiver -> 1400
    Welcome -> 1500


-----------------------------------------------------------------------------
-- MSG TYPES
-----------------------------------------------------------------------------

type CheckInMsg
  = UpdateMatchingAccts (Result Http.Error MatchingAcctInfo)
  | UpdateFlexId String
  | UpdateMemberNum Int

type CheckOutMsg
  = UpdateCheckedInAccts (Result Http.Error MatchingAcctInfo)
  | LogCheckOut Int
  | CheckOutSceneWillAppear

type CreatingAcctMsg
  = XcAcctCreationAttempted (Result Http.Error String)
  | CloneAttempted (Result Http.Error String)
  | CreatingAcctSceneWillAppear
  | IsAdultWasSet (Result Http.Error String)
  | DiscoveryMethodAdded (Result Http.Error String)

type HowDidYouHearMsg
  = AccDiscoveryMethods (Result Http.Error DiscoveryMethodInfo)  -- "Acc" means "accumulate"
  | ToggleDiscoveryMethod DiscoveryMethod

type MembersOnlyMsg
  = MembersOnlySceneWillAppear

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

type ReasonForVisitMsg
  = UpdateReasonForVisit ReasonForVisit
  | ValidateReason
  | LogCheckInResult (Result Http.Error GenericResult)
  | ReasonForVisitSceneWillAppear

type TaskListMsg
  = TaskListSceneWillAppear
  | CalendarPageResult (Result Http.Error CalendarPage)
  | ToggleTask OpsTask
  | ValidateTaskChoice

type WaiverMsg
  = ShowSignaturePad String
  | ClearSignaturePad String
  | GetSignature
  | UpdateSignature String  -- String is a data URL representation of an image.
  | WaiverSceneWillAppear

type WelcomeMsg
  = WelcomeSceneWillAppear

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
  | TaskListVector TaskListMsg
  | WaiverVector WaiverMsg
  | WelcomeVector WelcomeMsg

type WizardMsg
  = Push Scene
  | RebaseTo Scene
  | Pop
  | Reset
  | SceneWillAppear Scene
  | Tick Time
