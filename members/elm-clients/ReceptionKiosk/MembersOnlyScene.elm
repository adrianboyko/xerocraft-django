
module ReceptionKiosk.MembersOnlyScene exposing (init, update, view, MembersOnlyModel)

-- Standard
import Html exposing (..)
import Html.Attributes exposing (..)
import Regex exposing (regex)
import Time exposing (Time)

-- Third Party
import String.Extra exposing (..)

-- Local
import MembersApi as MembersApi
import XerocraftApi as XcApi
import Wizard.SceneUtils exposing (..)
import ReceptionKiosk.Types exposing (..)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias MembersOnlyModel =
  { waitCount: Int
  , badNews : List String
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  (SceneUtilModel
    { a
    | membersOnlyModel : MembersOnlyModel
    }
  )

init : Flags -> (MembersOnlyModel, Cmd Msg)
init flags =
  let sceneModel =
    { waitCount = 0
    , badNews = []
    }
  in (sceneModel, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : MembersOnlyMsg -> KioskModel a -> (MembersOnlyModel, Cmd Msg)
update msg kioskModel =

  let
    sceneModel = kioskModel.membersOnlyModel

  in case msg of

    MembersOnlySceneWillAppear ->
      (sceneModel, Cmd.none)

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.membersOnlyModel
  in
    genericScene kioskModel
      "Members Only Time"
      "Is your membership up to date"
      (div []
        [ text ""
        ]
      )
      []  -- No buttons. Scene will automatically transition.
      sceneModel.badNews
