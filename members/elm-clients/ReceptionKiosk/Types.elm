module ReceptionKiosk.Types exposing (..)

-- Standard
import Http

-- Third Party
import Material
import List.Nonempty exposing (Nonempty)

-- Local
import ReceptionKiosk.Backend exposing (..)

-----------------------------------------------------------------------------
-- FLAGS
-----------------------------------------------------------------------------

type alias Flags =
  { csrfToken: String
  , orgName: String
  , bannerTopUrl: String
  , bannerBottomUrl: String
  , discoveryMethodsUrl: String
  , checkedInAcctsUrl: String
  , matchingAcctsUrl: String
  , logVisitEventUrl: String
  , logReasonForVisitUrl: String
  }

-----------------------------------------------------------------------------
-- SCENES
-----------------------------------------------------------------------------

type Scene
  = CheckIn
  | CheckInDone
  | CheckOut
  | CheckOutDone
  | DoYouHaveAcct
  | HowDidYouHear
  | NewMember
  | NewUser
  | ReasonForVisit
  | Waiver
  | Welcome

-----------------------------------------------------------------------------
-- MSG TYPES
-----------------------------------------------------------------------------

type CheckInMsg
  = UpdateMatchingAccts (Result Http.Error MatchingAcctInfo)
  | UpdateFlexId String
  | LogCheckIn Int
  | LogCheckInResult (Result Http.Error GenericResult)

type CheckOutMsg
  = UpdateCheckedInAccts (Result Http.Error MatchingAcctInfo)
  | LogCheckOut Int
  | CheckOutSceneWillAppear

type HowDidYouHearMsg
  = AccDiscoveryMethods (Result Http.Error DiscoveryMethodInfo)  -- "Acc" means "accumulate"
  | ToggleDiscoveryMethod DiscoveryMethod

type NewMemberMsg
  = UpdateFirstName String
  | UpdateLastName String
  | UpdateEmail String
  | ToggleIsAdult
  | Validate

type NewUserMsg
  = ValidateUserNameAndPw
  | ValidateUserNameUnique (Result Http.Error MatchingAcctInfo)
  | UpdateUserName String
  | UpdatePassword1 String
  | UpdatePassword2 String

type ReasonForVisitMsg
  = UpdateReasonForVisit ReasonForVisit
  | ValidateReason
  | LogReasonResult (Result Http.Error GenericResult)

type WaiverMsg
  = ShowSignaturePad String
  | ClearSignaturePad String
  | GetSignature
  | UpdateSignature String  -- String is a data URL representation of an image.
  | AccountCreationResult (Result Http.Error String)
  | WaiverSceneWillAppear

type WelcomeMsg
  = WelcomeSceneWillAppear

type Msg
  = MdlVector (Material.Msg Msg)
  | WizardVector WizardMsg
  | CheckInVector CheckInMsg
  | CheckOutVector CheckOutMsg
  | HowDidYouHearVector HowDidYouHearMsg
  | NewMemberVector NewMemberMsg
  | NewUserVector NewUserMsg
  | ReasonForVisitVector ReasonForVisitMsg
  | WaiverVector WaiverMsg
  | WelcomeVector WelcomeMsg

type WizardMsg
  = Push Scene
  | Pop
  | Reset
  | SceneWillAppear Scene
