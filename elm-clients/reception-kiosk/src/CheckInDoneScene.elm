
module CheckInDoneScene exposing (init, view, CheckInDoneModel)

-- Standard
import Html exposing (Html, text, div)
import Time exposing (Time)

-- Third Party

-- Local
import Types exposing (..)
import Wizard.SceneUtils exposing (..)


-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

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
view kioskModel =
  let sceneModel = kioskModel.checkInDoneModel
  in genericScene kioskModel
    "You're Checked In"
    "Have fun!"
    (vspace 40)
    [ButtonSpec "Ok" (WizardVector <| Reset)]
    [] -- Never any bad news for this scene


-----------------------------------------------------------------------------
-- TICK (called each second)
-----------------------------------------------------------------------------


