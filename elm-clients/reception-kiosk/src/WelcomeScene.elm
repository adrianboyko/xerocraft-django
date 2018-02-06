
module WelcomeScene exposing (init, view, WelcomeModel)

-- Standard
import Html exposing (Html, div, text, img, br)
import Html.Attributes exposing (src, width, style)

-- Third Party
import Material
import List.Nonempty exposing (Nonempty)

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
type alias KioskModel a =
  { a
  ------------------------------------
  | mdl : Material.Model
  , flags : Flags
  , sceneStack : Nonempty Scene
  ------------------------------------
  , welcomeModel : WelcomeModel
  }

init : Flags -> (WelcomeModel, Cmd Msg)
init flags = ({}, Cmd.none)

-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------


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
      , sceneButton kioskModel <| ButtonSpec "I'm new!" (WizardVector <| Push <| HowDidYouHear) True
      , vspace 70
      , text "If you've already signed up here or on our website:"
      , vspace 20
      , sceneButton kioskModel <| ButtonSpec "Check In" (WizardVector <| Push <| CheckIn) True
      , sceneButton kioskModel <| ButtonSpec "Check Out" (WizardVector <| Push <| CheckOut) True
      , vspace 150
      , img [src "/static/members/cactuses.png", bottomImgStyle] []
      ]
    )
    []  -- Buttons are woven into the rest of the content on this scene.
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