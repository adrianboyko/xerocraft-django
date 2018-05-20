
module UseBankedHoursScene exposing
  ( init
  , update
  , view
  , UseBankedHoursModel
  )

-- Standard
import Html exposing (..)
import Html.Attributes exposing (..)
import Regex exposing (regex)
import Time exposing (Time)
import Date exposing (Date)

-- Third Party
import String.Extra exposing (..)
import Material
import List.Nonempty exposing (Nonempty)

-- Local
import XerocraftApi as XcApi
import XisRestApi as XisApi exposing (..)
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import CalendarDate
import PointInTime exposing (PointInTime)


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  { a
  ------------------------------------
  | mdl : Material.Model
  , flags : Flags
  , sceneStack : Nonempty Scene
  ------------------------------------
  , useBankedHoursModel : UseBankedHoursModel
  , currTime : Time
  , xisSession : XisApi.Session Msg
  }


type PaymentInfoState
  = PresentingOptions
  | ExplainingHowToPayNow
  | PaymentInfoSent
  | SendingPaymentInfo


type alias UseBankedHoursModel =
  -------------- Req'd arguments:
  { member : Maybe Member
  -------------- Other state:
  , paymentInfoState : PaymentInfoState
  , badNews : List String
  }


init : Flags -> (UseBankedHoursModel, Cmd Msg)
init flags =
  let sceneModel =
    { member = Nothing
    , paymentInfoState = PresentingOptions
    , badNews = []
    }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

{- Will keep this simple, for now. This scene will appear if all of the following are true:
   (1) We know what type of time block we're in.
   (2) The time block is tagged as being for Supporting Members Only.
   (3) We have the user's membership info.
-}
useBankedHoursButNotMember :
  XisApi.Session a -> Member -> PointInTime -> Maybe TimeBlock -> List TimeBlockType -> Bool
useBankedHoursButNotMember
  xis member now nowBlock allTypes =

  let
    useBankedHoursStr = "Members Only"
    defaultBlockTypeName = case xis.defaultBlockType allTypes of
      Just bt -> bt.data.name
      Nothing -> ""
    isCurrent = case member.data.latestNonfutureMembership of
      Just m -> xis.coverTime [m] now
      Nothing -> False
    isUseBankedHours = case nowBlock of
      Just nb -> xis.blockHasType useBankedHoursStr allTypes nb
      Nothing -> defaultBlockTypeName == useBankedHoursStr
  in
    isUseBankedHours && not isCurrent


update : UseBankedHoursMsg -> KioskModel a -> (UseBankedHoursModel, Cmd Msg)
update msg kioskModel =

  let
    sceneModel = kioskModel.useBankedHoursModel
    xis = kioskModel.xisSession

  in case msg of

    UBH_Segue member ->

      let
        newSceneModel = { sceneModel | member = Just member }
      in
        (newSceneModel, Cmd.none)


    -- FAILURES --------------------



-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.useBankedHoursModel
    xis = kioskModel.xisSession
  in
    case sceneModel.member of

      Nothing ->
        errorView kioskModel missingArguments

      Just m ->

        genericScene kioskModel
          "Supporting Members Only"
          "We are not currently open to the public"
          (text "Hello!")
          []  -- No buttons here. They will be woven into content.
          []  -- No bad news. Scene will fail silently, but should log somewhere.


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

