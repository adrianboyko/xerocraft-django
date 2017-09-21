
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
import OpsApi as Ops exposing (TimeBlock, TimeBlockType)
import Wizard.SceneUtils exposing (..)
import ReceptionKiosk.Types exposing (..)


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias MembersOnlyModel =
  { currTimeBlock : Maybe TimeBlock
  , currTimeBlockTypes : List TimeBlockType
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
    , currTimeBlockTypes = []
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
          (sceneModel, segueTo CheckInDone)

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
        followUpCmd = getTimeBlockTypes kioskModel
      in
        ({sceneModel | badNews = [], currTimeBlock = currBlock }, followUpCmd)

    UpdateTimeBlocks (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

    UpdateTimeBlockTypes (Ok pageOfTimeBlockTypes) ->
      case sceneModel.currTimeBlock of

        Just currTimeBlock ->
          let
            allBlockTypes = pageOfTimeBlockTypes.results
            relatedBlockTypeIds = List.map Ops.getIdFromUrl currTimeBlock.types
            isRelatedBlockType x = List.member (Ok x.id) relatedBlockTypeIds
            currBlockTypes = List.filter isRelatedBlockType allBlockTypes
          in
            ({sceneModel | badNews = [], currTimeBlockTypes = currBlockTypes }, Cmd.none)

        Nothing ->
          let
            errMsgs = ["Current time block unexpectedly unavailable."]
            newSceneModel = {sceneModel | badNews = errMsgs}
          in
            (newSceneModel, segueTo CheckInDone)

    UpdateTimeBlockTypes (Err error) ->
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
        (
        [ case sceneModel.currTimeBlock of
            Nothing -> text "not in block"  -- This shouldn't appear b/c we should skip scene if so.
            Just block -> text block.startTime
        ]
        ++
        List.map (\x -> text x.name) sceneModel.currTimeBlockTypes
        )
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

getTimeBlockTypes : KioskModel a  -> Cmd Msg
getTimeBlockTypes kioskModel =
  let
    getTimeBlockTypesFn = Ops.getTimeBlockTypes kioskModel.flags
  in
    getTimeBlockTypesFn (MembersOnlyVector << UpdateTimeBlockTypes)
