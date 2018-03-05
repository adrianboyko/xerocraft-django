
module CheckOutDoneScene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , CheckOutDoneModel
  )

-- Standard
import Html exposing (Html, div, text)
import Time exposing (Time)

-- Third Party
import Material
import List.Nonempty exposing (Nonempty)

-- Local
import Types exposing (..)
import Wizard.SceneUtils exposing (..)
import XisRestApi as XisApi exposing (Member)

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
  , checkOutDoneModel : CheckOutDoneModel
  , xisSession : XisApi.Session Msg
  }

type alias CheckOutDoneModel =
  { member : Maybe Member
  }

init : Flags -> (CheckOutDoneModel, Cmd Msg)
init flags =
  ( {member = Nothing}
  , Cmd.none
  )


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> Scene -> (CheckOutDoneModel, Cmd Msg)
sceneWillAppear kioskModel appearing vanishing =
  if appearing == CheckOutDone
    then
      (kioskModel.checkOutDoneModel, rebase)
    else
      (kioskModel.checkOutDoneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : CheckOutDoneMsg -> KioskModel a -> (CheckOutDoneModel, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.checkOutDoneModel
    xis = kioskModel.xisSession

  in case msg of
    COD_Segue member ->
      ( { sceneModel | member = Just member}
      , send <| WizardVector <| Push CheckOutDone
      )


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let sceneModel = kioskModel.checkOutDoneModel
  in genericScene kioskModel
    "You're Checked Out"
    "Have a Nice Day!"
    (vspace 40)
    [ButtonSpec "Ok" msgForReset True]
    [] -- Never any bad news for this scene


-----------------------------------------------------------------------------
-- TICK (called each second)
-----------------------------------------------------------------------------

