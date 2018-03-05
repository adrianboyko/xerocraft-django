
module ErrorScene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , ErrorModel)

-- Standard
import Html exposing (Html, div, p, text)

-- Third Party
import Material
import List.Nonempty as NonEmpty exposing (Nonempty)

-- Local
import Types exposing (..)
import Wizard.SceneUtils exposing (..)


-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------


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
  , errorModel : ErrorModel
  }

type alias ErrorModel =
  { errorMessage : Maybe String
  }

init : Flags -> (ErrorModel, Cmd Msg)
init flags =
  ( { errorMessage = Nothing
    }
  , Cmd.none
  )


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> Scene -> (ErrorModel, Cmd Msg)
sceneWillAppear kioskModel appearing vanishing =
  let
    sceneModel = kioskModel.errorModel
  in
    if appearing == Error then
      (sceneModel, Cmd.none)
    else
      (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : ErrorMsg -> KioskModel a -> (ErrorModel, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.errorModel
  in
    case msg of

      -- This assumes that the scene currently on top of the stack caused the error.
      ERR_Segue errMsg ->
        ( { sceneModel
          | errorMessage = Just errMsg
          }
        , send <| WizardVector <| Push <| Error
        )

      ERR_ResetClicked ->
        ( sceneModel
        , send <| WizardVector <| Reset
        )


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.errorModel
  in
    errorView
      kioskModel
      (Maybe.withDefault "Unspecified Error" sceneModel.errorMessage)


-----------------------------------------------------------------------------
-- TICK (called each second)
-----------------------------------------------------------------------------

