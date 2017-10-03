
module MembersOnlyScene exposing
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
import MembersApi as MembersApi exposing (Membership)
import XerocraftApi as XcApi
import OpsApi as OpsApi exposing (TimeBlock, TimeBlockType)
import Wizard.SceneUtils exposing (..)
import CheckInScene exposing (CheckInModel)
import Types exposing (..)


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type Fetchable a
  = Pending
  | Received a
  | Failed String

received x =
  case x of
    Received _ -> True
    _ -> False

type alias MembersOnlyModel =
  { block : Fetchable (Maybe TimeBlock)
  , types : Fetchable (List TimeBlockType)
  , memberships : Fetchable (List Membership)
  , badNews : List String
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  (SceneUtilModel
    { a
    | membersOnlyModel : MembersOnlyModel
    , checkInModel : CheckInModel
    }
  )

init : Flags -> (MembersOnlyModel, Cmd Msg)
init flags =
  let sceneModel =
    { block = Pending
    , types = Pending
    , memberships = Pending
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
      let
        memberNum = kioskModel.checkInModel.memberNum
        cmd1 = getTimeBlocks kioskModel
        cmd2 = getMemberships kioskModel memberNum
        cmds = Cmd.batch [cmd1, cmd2]
      in
        (sceneModel, cmds)

    MembersOnly ->
      if received sceneModel.block || received sceneModel.memberships
        then (sceneModel, Cmd.none)  -- Show this scene.
        else (sceneModel, segueTo CheckInDone)  -- Not enough info, so skip it.

    _ ->
      (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : MembersOnlyMsg -> KioskModel a -> (MembersOnlyModel, Cmd Msg)
update msg kioskModel =

  let
    sceneModel = kioskModel.membersOnlyModel

  in case msg of

    -- SUCCESSFUL FETCHES --

    UpdateTimeBlocks (Ok pageOfTimeBlocks) ->
      let
        blocks = pageOfTimeBlocks.results
        nowBlocks = List.filter .isNow blocks
        currBlock = List.head nowBlocks
        followUpCmd = if List.isEmpty nowBlocks then Cmd.none else getTimeBlockTypes kioskModel
      in
        ({sceneModel | block = Received currBlock }, followUpCmd)

    UpdateTimeBlockTypes (Ok pageOfTimeBlockTypes) ->
      let
        impossibleNote = "Impossible. Block types are only requested AFTER block is successfully received."
        logImpossibleCase _ =  -- This needs to be a fn and not a constant, hence the "_" param.
          let _ = Debug.log impossibleNote sceneModel
          in (sceneModel, Cmd.none)
      in
        case sceneModel.block of

          Received Nothing -> logImpossibleCase ()
          Failed _ -> logImpossibleCase ()
          Pending -> logImpossibleCase ()

          Received (Just block) ->
            let
              allBlockTypes = pageOfTimeBlockTypes.results
              relatedBlockTypeIds = List.map OpsApi.getIdFromUrl block.types
              isRelatedBlockType x = List.member (Ok x.id) relatedBlockTypeIds
              currBlockTypes = List.filter isRelatedBlockType allBlockTypes
            in
              ({sceneModel | types = Received currBlockTypes }, Cmd.none)

    UpdateMemberships (Ok pageOfMemberships) ->
      let memberships = pageOfMemberships.results
      in ({sceneModel | memberships = Received memberships}, Cmd.none)


    -- FAILED FETCHES --

    UpdateTimeBlocks (Err error) ->
      let msg = Debug.log "Error getting time blocks: " (toString error)
      in ({sceneModel | block = Failed msg}, Cmd.none)

    UpdateTimeBlockTypes (Err error) ->
      let msg = Debug.log "Error getting time block types: " (toString error)
      in ({sceneModel | types = Failed msg}, Cmd.none)

    UpdateMemberships (Err error) ->
      let msg = Debug.log "Error getting memberships: " (toString error)
      in ({sceneModel | memberships = Failed msg}, Cmd.none)



-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.membersOnlyModel
  in
    genericScene kioskModel
      "Supporting Members Only"
      "Is your supporting membership up to date?"
      (div []
        (
        [ case sceneModel.block of
            Received Nothing -> text "not in block"  -- This shouldn't appear b/c we should skip scene if so.
            Received (Just block) -> text block.startTime
            _ -> text "Shouldn't happen."
        ]
        ++
        case sceneModel.types of
          Received types ->
            List.map (\x -> text x.name) types
          _ -> []
        )
      )
      []  -- No buttons. Scene will automatically transition.
      []  -- No bad news. Scene will fail silently, but should log somewhere.


-----------------------------------------------------------------------------
-- COMMANDS
-----------------------------------------------------------------------------

getTimeBlocks : KioskModel a -> Cmd Msg
getTimeBlocks kioskModel =
  OpsApi.getTimeBlocks
    kioskModel.flags
    (MembersOnlyVector << UpdateTimeBlocks)

getTimeBlockTypes : KioskModel a  -> Cmd Msg
getTimeBlockTypes kioskModel =
  OpsApi.getTimeBlockTypes
    kioskModel.flags
    (MembersOnlyVector << UpdateTimeBlockTypes)

getMemberships : KioskModel a -> Int -> Cmd Msg
getMemberships kioskModel memberNum =
  MembersApi.getMemberships
    kioskModel.flags
    memberNum
    (MembersOnlyVector << UpdateMemberships)
