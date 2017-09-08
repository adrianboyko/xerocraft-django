
module ReceptionKiosk.VolunteerInDoneScene exposing (init, view, VolunteerInDoneModel)

-- Standard
import Html exposing (Html, text, div)

-- Third Party

-- Local
import Wizard.SceneUtils exposing (..)
import ReceptionKiosk.Types exposing (..)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- TODO: There should be a time out back to Welcome

type alias VolunteerInDoneModel =
  {
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a = (SceneUtilModel {a | volunteerInDoneModel : VolunteerInDoneModel})

init : Flags -> (VolunteerInDoneModel, Cmd Msg)
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
    "Here are your next steps"
    (div []
      [ vspace 50
      , text "Under Construction!"
      , vspace 50
      ]
    )
    [ButtonSpec "Ok" (WizardVector <| Push <| Welcome)]

