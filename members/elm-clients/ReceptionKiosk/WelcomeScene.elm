
module ReceptionKiosk.WelcomeScene exposing (init, update, view, WelcomeModel)

-- Standard
import Html exposing (Html, div, text, img, br)
import Html.Attributes exposing (src, width, style)

-- Third Party

-- Local
import Wizard.SceneUtils exposing (..)
import ReceptionKiosk.Types exposing (..)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias WelcomeModel =
  {
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a = (SceneUtilModel {a | welcomeModel : WelcomeModel})

init : Flags -> (WelcomeModel, Cmd Msg)
init flags = ({}, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : WelcomeMsg -> KioskModel a -> (WelcomeModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.welcomeModel
  in case msg of

    WelcomeSceneWillAppear ->
      let sceneModel = kioskModel.welcomeModel
      in (sceneModel, send (WizardVector <| Reset))

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  genericScene kioskModel
    "Welcome!"
    "Choose one of the following:"
    (div [sceneTextStyle]
      [ vspace 50
      , text "If you've never signed up here or on our website:"
      , vspace 20
      , sceneButton kioskModel <| ButtonSpec "I'm new!" (WizardVector <| Push <| HowDidYouHear)
      , vspace 70
      , text "If you've already signed up here or on our website:"
      , vspace 20
      , sceneButton kioskModel <| ButtonSpec "Check In" (WizardVector <| Push <| CheckIn)
      , sceneButton kioskModel <| ButtonSpec "Check Out" (WizardVector <| Push <| CheckOut)
      , vspace 150
      , img [src "/static/members/cactuses.png", bottomImgStyle] []
      ]
    )
    []  -- Buttons are woven into the rest of the content on this scene.
    []  -- Never any bad news for this scene.

bottomImgStyle = style
  [ "text-align" => "center"
  , "padding-left" => "30px"
  , "padding-right" => "0"
  ]