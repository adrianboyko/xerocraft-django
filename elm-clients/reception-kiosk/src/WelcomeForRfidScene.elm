
module WelcomeForRfidScene exposing
  ( init
  , update
  , view
  , WelcomeForRfidModel
  )

-- Standard
import Html exposing (Html, div, text, img, br)
import Html.Attributes exposing (src, width, style)

-- Third Party
import Material
import List.Nonempty as NonEmpty

-- Local
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import XisRestApi as XisApi exposing (Member)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  { a
  ------------------------------------
  | mdl : Material.Model
  , flags : Flags
  , sceneStack : NonEmpty.Nonempty Scene
  ------------------------------------
  , welcomeForRfidModel : WelcomeForRfidModel
  , xisSession : XisApi.Session Msg
  }

type alias WelcomeForRfidModel =
  { member : Maybe Member
  }


init : Flags -> (WelcomeForRfidModel, Cmd Msg)
init flags = (
  { member = Nothing
  }
  ,
  Cmd.none
  )


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : WelcomeForRfidMsg -> KioskModel a -> (WelcomeForRfidModel, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.welcomeForRfidModel
    xis = kioskModel.xisSession

  in case msg of

    W4R_Segue member ->
      ( {sceneModel | member = Just member}
      , send <| WizardVector <| Push <| WelcomeForRfid
      )

    W4R_CheckInClicked ->
      ( sceneModel
      , case sceneModel.member of
          Just m -> send <| ReasonForVisitVector <| R4V_Segue m
          Nothing -> send <| ErrorVector <| ERR_Segue missingArguments
      )

    W4R_CheckOutClicked ->
      ( sceneModel
      , case sceneModel.member of
          Just m -> send <| OldBusinessVector <| OB_SegueA CheckOutSession m
          Nothing -> send <| ErrorVector <| ERR_Segue missingArguments
      )


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    button = sceneButton kioskModel
    sceneModel = kioskModel.welcomeForRfidModel
    friendlyName =
      Maybe.withDefault "ERR"
        <| Maybe.map (.data >> .friendlyName) sceneModel.member
  in genericScene kioskModel
    ("Welcome "++ friendlyName ++"!")
    "Choose one of the following:"
    (div [sceneTextStyle]
      [ vspace 225
      , button <| ButtonSpec "Check In" (WelcomeForRfidVector <| W4R_CheckInClicked) True
      , button <| ButtonSpec "Check Out" (WelcomeForRfidVector <| W4R_CheckOutClicked) True
      , ( case sceneModel.member of
            Just m ->
              if List.member m.id [1, 1842] then  -- beta testers
                div []
                  [ vspace 40
                  , sceneButton kioskModel <| ButtonSpec "Give Me Soda!" (DispenseSodaVector <| DS_Segue m) True
                  ]
              else
                 text ""
            Nothing -> text ""
        )
      , vspace 225
      , img [src "/static/members/cactuses.png", bottomImgStyle] []
      ]
    )
    []  -- Buttons are woven into the content of the welcome text.
    []  -- Never any bad news for this scene.


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

bottomImgStyle = style
  [ "text-align" => "center"
  , "padding-left" => "30px"
  , "padding-right" => "0"
  ]