
module ReceptionKiosk.CheckInDoneScene exposing (init, view, CheckInDoneModel)

-- Standard
import Html exposing (Html, text)

-- Third Party

-- Local
import ReceptionKiosk.Types exposing (..)
import Wizard.SceneUtils exposing (..)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- TODO: There should be a time out back to Welcome

type alias CheckInDoneModel =
  {
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a = (SceneUtilModel {a | checkInDoneModel : CheckInDoneModel})

init : Flags -> (CheckInDoneModel, Cmd Msg)
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
    "You're Checked In"
    "Have fun!"
    (text "")
    [ButtonSpec "Ok" (WizardVector <| Push <| Welcome)]
    []
