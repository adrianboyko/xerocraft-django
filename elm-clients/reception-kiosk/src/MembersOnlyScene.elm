
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
import Fetchable exposing (..)


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias MembersOnlyModel =
  { nowBlock : Fetchable (Maybe TimeBlock)
  , allTypes : Fetchable (List TimeBlockType)
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
    { nowBlock = Pending
    , allTypes = Pending
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
        cmd3 = getTimeBlockTypes kioskModel
        cmds = Cmd.batch [cmd1, cmd2, cmd3]
      in
        (sceneModel, cmds)

    MembersOnly ->
      if haveSomethingToSay kioskModel
        then (sceneModel, Cmd.none)  -- Show this scene.
        else (sceneModel, segueTo CheckInDone)  -- Skip it.

    _ ->
      (sceneModel, Cmd.none)

{- Will keep this simple, for now. This scene will appear if all of the following are true:
   (1) We know what type of time block we're in.
   (2) The time block is tagged as being for Supporting Members Only.
   (3) We have the user's membership info.
-}
haveSomethingToSay : KioskModel a -> Bool
haveSomethingToSay kioskModel =
  let
    sceneModel = kioskModel.membersOnlyModel
    membersOnlyStr = "Members Only"
  in
    case (sceneModel.nowBlock, sceneModel.allTypes, sceneModel.memberships) of

      -- Following is the case where somebody arrives during an explicit time block.
      (Received (Just nowBlock), Received allTypes, Received memberships) ->
        let nowBlockTypes = OpsApi.blocksTypes nowBlock allTypes
        in List.member membersOnlyStr (List.map .name nowBlockTypes)

      -- Following is the case where we're not in any explicit time block.
      -- So use default time block type, if one has been specified.
      (Received Nothing, Received allTypes, Received memberships) ->
        let defaultBlockType = OpsApi.defaultType allTypes
        in case defaultBlockType of
          Just bt -> bt.name == membersOnlyStr
          Nothing -> False

      _ -> False


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
        nowBlock = List.head nowBlocks
      in
        ({sceneModel | nowBlock = Received nowBlock }, Cmd.none)

    UpdateTimeBlockTypes (Ok pageOfTimeBlockTypes) ->
      ({sceneModel | allTypes = Received pageOfTimeBlockTypes.results}, Cmd.none)

    UpdateMemberships (Ok pageOfMemberships) ->
      let memberships = pageOfMemberships.results
      in ({sceneModel | memberships = Received memberships}, Cmd.none)


    -- FAILED FETCHES --

    UpdateTimeBlocks (Err error) ->
      let msg = toString error |> Debug.log "Error getting time blocks: "
      in ({sceneModel | nowBlock = Failed msg}, Cmd.none)

    UpdateTimeBlockTypes (Err error) ->
      let msg = toString error |> Debug.log "Error getting time block types: "
      in ({sceneModel | allTypes = Failed msg}, Cmd.none)

    UpdateMemberships (Err error) ->
      let msg = toString error |> Debug.log "Error getting memberships: "
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
      (
      case sceneModel.memberships of

        Received memberships ->
          case membershipStatus memberships of

            Current -> text ""
            ExpiredRecently -> text ""
            ExpiredLongAgo -> text ""
            Never -> text ""

        _ -> text ""
      )
      []  -- No buttons. Scene will automatically transition.
      []  -- No bad news. Scene will fail silently, but should log somewhere.


type MembershipStatus
  = Current
  | ExpiredRecently
  | ExpiredLongAgo
  | Never

membershipStatus : List Membership -> MembershipStatus
membershipStatus memberships =
  case memberships of

    [] ->
      Never

    membership::_ ->
      Current

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
