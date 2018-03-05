
module EmailInUseScene exposing (init, update, view, EmailInUseModel)

-- Standard
import Html exposing (Html, text, div, br, span)
import Html.Attributes exposing (style)
import Color exposing (rgb)

-- Third Party
import Material
import List.Nonempty exposing (Nonempty)

-- Local
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import XisRestApi as XisApi exposing (Member)


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  { a
  ------------------------------------
  | mdl : Material.Model
  , flags : Flags
  , sceneStack : Nonempty Scene
  ------------------------------------
  , emailInUseModel : EmailInUseModel
  }


type alias EmailInUseModel =
  ------------- Req'd Args:
  { membersUsingAddr : Maybe (List Member)
  }


init : Flags -> (EmailInUseModel, Cmd Msg)
init flags =
  ({membersUsingAddr = Nothing}, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : EmailInUseMsg -> KioskModel a -> (EmailInUseModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.emailInUseModel
  in case msg of

    EIU_Segue members ->
      ( { sceneModel | membersUsingAddr = Just members }
      , send <| WizardVector <| Push EmailInUse
      )

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  case kioskModel.emailInUseModel.membersUsingAddr of

    Nothing ->
      errorView kioskModel missingArguments

    Just membersUsing ->
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
            List.map (\m -> span [userIdStyle] [text m.data.userName]) membersUsing
            ++
            [ vspace 50
            , text "If you recognize one of them as yours,"
            , br [] []
            , text "please remember it and use it to:"
            , vspace 20
            , sceneButton kioskModel <| ButtonSpec "Check In" (WizardVector <| Push <| CheckIn) True
            , vspace 50
            , text "If you don't recognize any of them"
            , br [] []
            , text "please speak to a staff member."
            , vspace 20
            , sceneButton kioskModel <| ButtonSpec "OK" (WizardVector <| Reset) True
            ]
          )
        )
        []  -- Buttons for this scene are woven into the scene content.
        []  -- Never any bad news for this scene

