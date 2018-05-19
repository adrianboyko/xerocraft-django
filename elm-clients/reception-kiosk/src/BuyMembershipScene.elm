
module BuyMembershipScene exposing
  ( init
  , update
  , view
  , BuyMembershipModel
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
  , buyMembershipModel : BuyMembershipModel
  , xisSession : XisApi.Session Msg
  }



type alias BuyMembershipModel =
  -------------- Req'd arguments:
  { member : Maybe Member
  -------------- Other state:
  , badNews : List String
  }


init : Flags -> (BuyMembershipModel, Cmd Msg)
init flags =
  let sceneModel =
    { member = Nothing
    , badNews = []
    }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : BuyMembershipMsg -> KioskModel a -> (BuyMembershipModel, Cmd Msg)
update msg kioskModel =

  let
    sceneModel = kioskModel.buyMembershipModel
    xis = kioskModel.xisSession

  in case msg of

    BM_Segue member ->
      let
        newSceneModel =
          { sceneModel
          | member = Just member
          }
      in
        (newSceneModel, send <| WizardVector <| Push BuyMembership)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.buyMembershipModel
    xis = kioskModel.xisSession
  in
    case sceneModel.member of

      Nothing ->
        errorView kioskModel missingArguments

      Just m ->

        genericScene kioskModel
          "Buy a Membership"
          "Please ask a Staffer for Assistance"
          ( div [sceneTextStyle, sceneTextBlockStyle]
             [ vspace 40
             , img [src "/static/bzw_ops/VisaMcDiscAmexCashCheck.png", payTypesImgStyle] []
             , vspace 60
             , text "We accept credit card, cash, and checks."
             , vspace 0
             , text "Ask our staff to help you process the payment."
             ]
          )
          [ ButtonSpec "I Did It!" (OldBusinessVector <| OB_SegueA CheckInSession m) True
          , ButtonSpec "No Thanks" (WizardVector <| Pop) True]
          []  -- No bad news.


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

payTypesImgStyle = style
  [ "text-align" => "center"
  , "width" => px 400
  ]
