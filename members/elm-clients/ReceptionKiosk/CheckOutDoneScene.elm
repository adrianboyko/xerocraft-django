
module ReceptionKiosk.CheckOutDoneScene exposing (init, view)

-- Standard
import Html exposing (Html, text)

-- Third Party

-- Local
import ReceptionKiosk.Types exposing (..)
import ReceptionKiosk.SceneUtils exposing (..)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- TODO: There should be a time out back to Welcome

init : Flags -> (CheckOutDoneModel, Cmd Msg)
init flags = ({}, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : Model -> Html Msg
view model =
  genericScene model
    "You're Checked Out"
    "Have a Nice Day!"
    (text "")
    [ButtonSpec "OK" (Push Welcome)]

