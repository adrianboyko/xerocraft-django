
module CheckInScene exposing
  ( init
  , sceneWillAppear
  , view
  , update
  , tick
  , CheckInModel
  )

-- Standard
import Html exposing (Html, div, text, audio)
import Html.Attributes exposing (src, autoplay)
import Http
import Time exposing (Time)

-- Third Party
import Material
import Material.Chip as Chip
import Material.Options as Options exposing (css)

-- Local
import Types exposing (..)
import Wizard.SceneUtils exposing (..)
import MembersApi as MembersApi
import XisRestApi as XisApi

-- TODO: Before user types flexid, could show usernames of recent RFID swipers?
-- TODO: If user is signing in after acct creation, show a username hint?


-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- REVIEW: Strictly speaking, flexID and memberNum should be Maybes.
type alias CheckInModel =
  { flexId : String  -- UserName or surname.
  , matches : List MembersApi.MatchingAcct  -- Matches to username/surname
  , memberNum : Int -- The member number that the person chose to check in as.
  , badNews : List String
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a = (SceneUtilModel {a | checkInModel : CheckInModel})

init : Flags -> (CheckInModel, Cmd Msg)
init flags =
  let model =
    { flexId = ""  -- A harmless initial value.
    , matches = []
    , memberNum = -99  -- A harmless initial value.
    , badNews = []
    }
  in (model, Cmd.none)


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (CheckInModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  if appearingScene == CheckIn
    then
      let
        cmd1 = getRecentRfidEntriesCmd kioskModel
        cmd2 = focusOnIndex idxFlexId
        cmd = Cmd.batch [cmd1, cmd2]
      in
        (kioskModel.checkInModel, cmd)
    else
      (kioskModel.checkInModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : CheckInMsg -> KioskModel a -> (CheckInModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.checkInModel
  in case msg of

    UpdateFlexId rawId ->
      let
        id = XisApi.djangoizeId rawId
        getMatchingAccts = MembersApi.getMatchingAccts kioskModel.flags
      in
        if (String.length id) > 1
        then
          ( {sceneModel | flexId=id}
          , getMatchingAccts id (CheckInVector << UpdateMatchingAccts)
          )
        else
          ( {sceneModel | matches=[], flexId=id}
          , Cmd.none
          )

    UpdateMatchingAccts (Ok {target, matches}) ->
      if target == sceneModel.flexId
      then ({sceneModel | matches = matches, badNews = []}, Cmd.none)
      else (sceneModel, Cmd.none)

    UpdateMatchingAccts (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

    UpdateMemberNum memberNum ->
      ({sceneModel | memberNum = memberNum}, segueTo OldBusiness)

    CheckInShortcut userName memberNum ->
      ({sceneModel | flexId=userName, memberNum=memberNum}, segueTo OldBusiness)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

idxCheckInScene = mdlIdBase CheckIn
idxFlexId = [idxCheckInScene, 1]

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.checkInModel
    clickMsg = \acct -> CheckInVector <| UpdateMemberNum <| acct.memberNum
    acctToChip = \acct ->
      Chip.button
        [Options.onClick (clickMsg acct)]
        [Chip.content [] [text acct.userName]]

  in genericScene kioskModel
    "Let's Get You Checked-In!"
    "Who are you?"
    ( div []
        (List.concat
          [ [sceneTextField kioskModel idxFlexId "Enter your Userid or Last Name" sceneModel.flexId (CheckInVector << UpdateFlexId), vspace 0]
          , if List.length sceneModel.matches > 0
             then [vspace 50, text "Tap your userid if you see it below:", vspace 20]
             else [vspace 0]
          , List.map acctToChip sceneModel.matches
          , [ vspace (if List.length sceneModel.badNews > 0 then 40 else 0) ]
          , if not (List.isEmpty sceneModel.matches)
             then
               -- TODO: Audio tag lag can be very bad. See https://lowlag.alienbill.com/
               [audio [src "/static/members/beep-22.mp3", autoplay True] []]
             else
               [vspace 0]
          ]
        )
    )
    []  -- No buttons
    sceneModel.badNews


-----------------------------------------------------------------------------
-- TICK (called each second)
-----------------------------------------------------------------------------

tick : Time -> KioskModel a -> (CheckInModel, Cmd Msg)
tick time kioskModel =
  let
    sceneModel = kioskModel.checkInModel
    visible = sceneIsVisible kioskModel CheckIn
    inc = if visible then 1 else 0
    cmd1 =
      if visible && String.isEmpty sceneModel.flexId
        then getRecentRfidEntriesCmd kioskModel
        else Cmd.none
    cmd = if visible then cmd1 else Cmd.none
  in
    (sceneModel, cmd)


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- COMMANDS
-----------------------------------------------------------------------------

getRecentRfidEntriesCmd kioskModel =
  MembersApi.getRecentRfidEntries
    kioskModel.flags
    (CheckInVector << UpdateMatchingAccts)

-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

sceneChipCss =
  [ css "margin-left" "3px"
  , css "margin-right" "3px"
  ]
