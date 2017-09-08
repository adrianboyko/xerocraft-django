
module ReceptionKiosk.VolunteerInDoneScene exposing (init, view, VolunteerInDoneModel)

-- Standard
import Html exposing (Html, text, div, p)
import Html.Attributes exposing (style)

-- Third Party

-- Local
import Wizard.SceneUtils exposing (..)
import ReceptionKiosk.Types exposing (..)
import ReceptionKiosk.VolunteerInScene exposing (VolunteerInModel)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- TODO: There should be a time out back to Welcome

type alias VolunteerInDoneModel =
  {
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  SceneUtilModel
    { a
    | volunteerInDoneModel : VolunteerInDoneModel
    , volunteerInModel : VolunteerInModel
    }

init : Flags -> (VolunteerInDoneModel, Cmd Msg)
init flags = ({}, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.volunteerInDoneModel
    volunteerInModel = kioskModel.volunteerInModel
    instructions =
      case volunteerInModel.selectedTask of
        Just opsTask -> opsTask.instructions
        Nothing -> "Please see a Staff Member."
  in
    genericScene kioskModel
      "You're Checked In!"
      "Instructions Follow:"
      (div [instructionDiv]
        [ vspace 20
        , p [instructionPara] [text instructions]
        , vspace 30
        , text "When the task is completed, return to this kiosk and use Check Out to close it."
        , vspace 20
        ]
      )
      [ButtonSpec "Got It!" (WizardVector <| Push <| Welcome)]


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

instructionDiv = style
  [ "width" => "650px"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "line-height" => "1"
  ]

instructionPara = style
  [ "font-size" => "16pt"
  ]
