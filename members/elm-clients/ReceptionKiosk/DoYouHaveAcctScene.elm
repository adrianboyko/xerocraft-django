
module ReceptionKiosk.DoYouHaveAcctScene exposing (init, view)

-- Standard
import Html exposing (Html, text)

-- Third Party

-- Local
import ReceptionKiosk.Types exposing (..)
import ReceptionKiosk.SceneUtils exposing (..)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

init : Flags -> (DoYouHaveAcctModel, Cmd Msg)
init flags = ({}, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : Model -> Html Msg
view kioskModel =
  genericScene kioskModel
    "Great!"
    "Do you already have an account here or on our website?"
    (text "")
    [ ButtonSpec "Yes" (Push CheckIn)
    , ButtonSpec "No" (Push NewMember)
    -- TODO: How about a "I don't know" button, here?
    ]
