
module YouCantEnterScene exposing
  ( init
  , update
  , view
  , YouCantEnterModel
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
  , youCantEnterModel : YouCantEnterModel
  , xisSession : XisApi.Session Msg
  }



type alias YouCantEnterModel =
  -------------- Req'd arguments:
  { member : Maybe Member
  -------------- Other state:
  , badNews : List String
  }


init : Flags -> (YouCantEnterModel, Cmd Msg)
init flags =
  let sceneModel =
    { member = Nothing
    , badNews = []
    }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : YouCantEnterMsg -> KioskModel a -> (YouCantEnterModel, Cmd Msg)
update msg kioskModel =

  let
    sceneModel = kioskModel.youCantEnterModel
    xis = kioskModel.xisSession

  in case msg of

    YCE_Segue member ->
      let
        newSceneModel =
          { sceneModel
          | member = Just member
          }
      in
        (newSceneModel, send <| WizardVector <| Push YouCantEnter)

    PayNowAtFrontDesk member ->
      -- TODO: Send a text to the staffer so they can help?
      (sceneModel, send <| BuyMembershipVector <| BM_Segue member)

    AlreadyPaid member ->
      -- TODO: Log the member's claim? Send a text to the staffer so they can verify?
      (sceneModel, send <| OldBusinessVector <| OB_SegueA CheckInSession member)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.youCantEnterModel
    xis = kioskModel.xisSession
  in
    case sceneModel.member of

      Nothing ->
        errorView kioskModel missingArguments

      Just m ->

        genericScene kioskModel
          "Supporting Members Only"
          "We are not currently open to the public"
          (optionsContent kioskModel sceneModel xis m)
          []  -- No buttons here. They will be woven into content.
          []  -- No bad news. Scene will fail silently, but should log somewhere.


optionsContent : KioskModel a -> YouCantEnterModel -> XisApi.Session Msg -> Member -> Html Msg
optionsContent kioskModel sceneModel xis member =
  let
    paymentMsg = case member.data.latestNonfutureMembership of
      Just mship ->
        "Our records show that your most recent membership expired on "
        ++ CalendarDate.format "%d-%b-%Y" mship.data.endDate
        ++ "."
      Nothing ->
        ""
  in
    div [sceneTextStyle, sceneTextBlockStyle]
        [ vspace 30
        , text "If you wish to use Xerocraft at this time, you need to have a paid membership. So, what would you like to do? Choose below:"
        , vspace 60
        , sceneButton kioskModel
            (ButtonSpec
               "Come back during public hours"
               (PublicHoursVector <| PH_Segue member)
               True
            )
        , vspace 30
        , sceneButton kioskModel
            (ButtonSpec
               "Pay now at front desk"
               (YouCantEnterVector <| PayNowAtFrontDesk member)
               True
            )
        , vspace 30
        , sceneButton kioskModel
            (ButtonSpec
               "Hold on, I already paid!"
               (YouCantEnterVector <| AlreadyPaid member)
               True
            )
        , vspace 60
        , text paymentMsg
        ]


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------
