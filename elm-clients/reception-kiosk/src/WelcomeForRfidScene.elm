
module WelcomeForRfidScene exposing (init, view, WelcomeForRfidModel)

-- Standard
import Html exposing (Html, div, text, img, br)
import Html.Attributes exposing (src, width, style)

-- Third Party
import Material
import List.Nonempty as NonEmpty

-- Local
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
  , sceneStack : NonEmpty.Nonempty Scene
  ------------------------------------
  , welcomeForRfidModel : WelcomeForRfidModel
  }

type alias WelcomeForRfidModel =
  {
  }


init : Flags -> (WelcomeForRfidModel, Cmd Msg)
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
  let button = sceneButton kioskModel
  in genericScene kioskModel
    "Welcome!"
    "Choose one of the following:"
    (div [sceneTextStyle]
      [ vspace 225
      , button <| ButtonSpec "Check In" (WizardVector <| Push <| CheckIn) True
      , button <| ButtonSpec "Check Out" (WizardVector <| Push <| CheckOut) True
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