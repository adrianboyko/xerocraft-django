
module ReceptionKiosk.DoYouHaveAcctScene exposing (init, view, DoYouHaveAcctModel)

-- Standard
import Html exposing (Html, text)

-- Third Party

-- Local
import ReceptionKiosk.Types exposing (..)
import ReceptionKiosk.SceneUtils exposing (..)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias DoYouHaveAcctModel =
  {
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a = (SceneUtilModel {a | doYouHaveAcctModel : DoYouHaveAcctModel})

init : Flags -> (DoYouHaveAcctModel, Cmd Msg)
init flags = ({}, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  genericScene kioskModel
    "Great!"
    "Do you already have an account here or on our website?"
    (text "")
    [ ButtonSpec "Yes" (WizardVector <| Push <| CheckIn)
    , ButtonSpec "No" (WizardVector <| Push <| NewMember)
    -- TODO: How about a "I don't know" button, here?
    ]
