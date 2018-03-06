
module SignUpDoneScene exposing (init, sceneWillAppear, update, view, SignUpDoneModel)

-- Standard
import Html exposing (Html, text, p, br, span)

-- Third Party
import Material
import Material.Options as Options exposing (css)
import List.Nonempty exposing (Nonempty)

-- Local
import Wizard.SceneUtils exposing (..)
import Types exposing (..)


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
  , signUpDoneModel : SignUpDoneModel
  }


type alias SignUpDoneModel =
  { userName : Maybe String
  }


init : Flags -> (SignUpDoneModel, Cmd Msg)
init flags =
  ( {userName=Nothing}
  , Cmd.none)


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> Scene -> (SignUpDoneModel, Cmd Msg)
sceneWillAppear kioskModel appearing vanishing =
  let
    sceneModel = kioskModel.signUpDoneModel
  in
    case (appearing, vanishing) of

      (SignUpDone, _) ->
        (sceneModel, send (WizardVector <| Rebase))

      _ ->
        (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : SignUpDoneMsg -> KioskModel a -> (SignUpDoneModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.signUpDoneModel
  in case msg of

    SUD_Segue userName ->
      ( { sceneModel
        | userName = Just userName
        }
      , send <| WizardVector <| Push <| SignUpDone
      )


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.signUpDoneModel
  in
    case sceneModel.userName of

    Just uName ->
      genericScene kioskModel
        "Xerocraft Account Created!"
        "Just one more thing..."
        (p [sceneTextStyle]
          [ vspace 30
          , text "You must check in each time you visit"
          , br [] []
          , text "so please remember that your userid is:"
          , vspace 40
          , span [userIdStyle] [text uName]
          , vspace 40
          , text "Click the button below to check in now!"
          ]
        )
        [ButtonSpec "Check In" (WizardVector <| Push <| CheckIn) True]
        []  -- Never any bad news for this scene

    _ -> errorView kioskModel missingArguments
