
module ReceptionKiosk.MembersOnlyScene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , MembersOnlyModel
  , getTimeBlocks
  )

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
import OpsApi as Ops
import Wizard.SceneUtils exposing (..)
import ReceptionKiosk.Types exposing (..)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias MembersOnlyModel =
  { currTimeBlock : Maybe Ops.TimeBlock
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
    { currTimeBlock = Nothing
    , badNews = []
    }
  in (sceneModel, Cmd.none)

-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (MembersOnlyModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  let sceneModel = kioskModel.membersOnlyModel
  in case appearingScene of

    ReasonForVisit ->
      -- We want to have the current time block on hand by the time MembersOnly
      -- appears, so start the fetch when ReasonForVisit appears.
      (sceneModel, getTimeBlocks kioskModel)

    MembersOnly ->
      case sceneModel.currTimeBlock of
        Just block ->
          (sceneModel, Cmd.none)
        Nothing ->
          (sceneModel, send (WizardVector <| Push <| CheckInDone))

    _ ->
      (kioskModel.membersOnlyModel, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : MembersOnlyMsg -> KioskModel a -> (MembersOnlyModel, Cmd Msg)
update msg kioskModel =

  let
    sceneModel = kioskModel.membersOnlyModel

  in case msg of

    UpdateTimeBlocks (Ok pageOfTimeBlocks) ->
      let
        blocks = pageOfTimeBlocks.results
        nowBlocks = List.filter .isNow blocks
        currBlock = List.head nowBlocks
      in
        ({sceneModel | badNews = [], currTimeBlock = currBlock }, Cmd.none)

    UpdateTimeBlocks (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

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
      "Is your membership up to date?"
      (div []
        [ case sceneModel.currTimeBlock of
            Nothing -> text "not in block"
            Just block -> text block.startTime
        ]
      )
      []  -- No buttons. Scene will automatically transition.
      []  -- No bad news. Scene will fail silently, but should log somewhere.

-----------------------------------------------------------------------------
-- PREP CMDS (which are called by init or earlier scenes)
-----------------------------------------------------------------------------

getTimeBlocks : KioskModel a -> Cmd Msg
getTimeBlocks kioskModel =
  let
    getTimeBlocksFn = Ops.getTimeBlocks kioskModel.flags
  in
    getTimeBlocksFn (MembersOnlyVector << UpdateTimeBlocks)