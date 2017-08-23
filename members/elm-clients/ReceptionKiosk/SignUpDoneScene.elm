
module ReceptionKiosk.SignUpDoneScene exposing (init, view, SignUpDoneModel)

-- Standard
import Html exposing (Html, text, p, br)

-- Third Party
import Material.Options as Options exposing (css)

-- Local
import ReceptionKiosk.Types exposing (..)
import ReceptionKiosk.SceneUtils exposing (..)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- TODO: There should be a time out back to Welcome

type alias SignUpDoneModel =
  {
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a = (SceneUtilModel {a | signUpDoneModel : SignUpDoneModel})

init : Flags -> (SignUpDoneModel, Cmd Msg)
init flags = ({}, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view model =
  genericScene model
    "Xerocraft Account Created!"
    "Just one more thing..."
    (p [sceneTextStyle]
      [ vspace 50
      , text "Each time you visit, you must check in."
      , br [] []
      , text "Click the button below to do that now!"
      , vspace 10
      ]
    )
    [ButtonSpec "Check In" (WizardVector <| Push <| CheckIn)]

