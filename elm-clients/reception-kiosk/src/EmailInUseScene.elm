
module EmailInUseScene exposing (init, view, EmailInUseModel)

-- Standard
import Html exposing (Html, text, div, br, span)
import Html.Attributes exposing (style)
import Color exposing (rgb)

-- Third Party

-- Local
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import NewMemberScene exposing (NewMemberModel)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- TODO: There should be a time out back to Welcome

type alias EmailInUseModel =
  {
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  (SceneUtilModel
    { a
    | newMemberModel : NewMemberModel
    , emailInUseModel : EmailInUseModel
    }
  )

init : Flags -> (EmailInUseModel, Cmd Msg)
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
    "Already Registered!"
    ""
    (div [sceneTextStyle]
      (
        [ vspace 30
        , text "The following accounts are using your email address:"
        , vspace 30
        ]
        ++
        List.map (\uid -> span [userIdStyle] [text uid]) kioskModel.newMemberModel.userIds
        ++
        [ vspace 50
        , text "If you recognize one of them as yours,"
        , br [] []
        , text "please remember it and use it to:"
        , vspace 20
        , sceneButton kioskModel <| ButtonSpec "Check In" (WizardVector <| Push <| CheckIn)
        , vspace 50
        , text "If you don't recognize any of them"
        , br [] []
        , text "please speak to a staff member."
        , vspace 20
        , sceneButton kioskModel <| ButtonSpec "Ok" (WizardVector <| Push <| Welcome)
        ]
      )
    )
    []  -- Buttons for this scene are woven into the scene content.
    []  -- Never any bad news for this scene

