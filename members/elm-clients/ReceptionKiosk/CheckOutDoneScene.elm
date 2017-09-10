
module ReceptionKiosk.CheckOutDoneScene exposing (init, view, CheckOutDoneModel)

-- Standard
import Html exposing (Html, text)

-- Third Party

-- Local
import ReceptionKiosk.Types exposing (..)
import Wizard.SceneUtils exposing (..)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias CheckOutDoneModel =
  {
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a = (SceneUtilModel {a | checkOutDoneModel : CheckOutDoneModel})

-- TODO: There should be a time out back to Welcome
init : Flags -> (CheckOutDoneModel, Cmd Msg)
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
    "You're Checked Out"
    "Have a Nice Day!"
    (text "")
    [ButtonSpec "OK" (WizardVector <| Push <| Welcome)]
    [] -- Never any bad news for this scene

