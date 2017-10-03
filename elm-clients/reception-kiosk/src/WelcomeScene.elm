
module WelcomeScene exposing (init, sceneWillAppear, view, WelcomeModel)

-- Standard
import Html exposing (Html, div, text, img, br)
import Html.Attributes exposing (src, width, style)

-- Third Party

-- Local
import Wizard.SceneUtils exposing (..)
import Types exposing (..)

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
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (WelcomeModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  if appearingScene == Welcome
    then
      let
        sceneModel = kioskModel.welcomeModel
        cmd1 = hideKeyboard ()
        cmd2 = send (WizardVector <| Reset)
        cmds = Cmd.batch [cmd1, cmd2]
      in (sceneModel, cmds)
    else
      (kioskModel.welcomeModel, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

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