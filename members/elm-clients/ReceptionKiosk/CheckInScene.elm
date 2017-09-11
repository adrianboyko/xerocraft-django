
module ReceptionKiosk.CheckInScene exposing (init, view, update, CheckInModel)

-- Standard
import Html exposing (Html, div, text, audio)
import Html.Attributes exposing (src, autoplay)

import Http

-- Third Party
import Material
import Material.Chip as Chip
import Material.Options as Options exposing (css)

-- Local
import ReceptionKiosk.Types exposing (..)
import Wizard.SceneUtils exposing (..)
import MembersApi as MembersApi

-- TODO: Before user types flexid, could show usernames of recent RFID swipers?
-- TODO: If user is signing in after acct creation, show a username hint?

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
-- UPDATE
-----------------------------------------------------------------------------

update : CheckInMsg -> KioskModel a -> (CheckInModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.checkInModel
  in case msg of

    UpdateFlexId rawId ->
      let
        id = MembersApi.djangoizeId rawId
        getMatchingAccts = MembersApi.getMatchingAccts kioskModel.flags
      in
        if (String.length id) > 1
        then
          ({sceneModel | flexId = id}, getMatchingAccts id (CheckInVector << UpdateMatchingAccts))
        else
          ({sceneModel | matches = [], flexId = id}, Cmd.none )

    UpdateMatchingAccts (Ok {target, matches}) ->
      if target == sceneModel.flexId
      then ({sceneModel | matches = matches, badNews = []}, Cmd.none)
      else (sceneModel, Cmd.none)

    UpdateMatchingAccts (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

    UpdateMemberNum memberNum ->
      ({sceneModel | memberNum = memberNum}, send (WizardVector <| Push <| ReasonForVisit))

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
          [ [sceneTextField kioskModel idxFlexId "Your Username or Surname" sceneModel.flexId (CheckInVector << UpdateFlexId), vspace 0]
          , if List.length sceneModel.matches > 0
             then [vspace 30, text "Tap your userid, below:", vspace 20]
             else [vspace 0]
          , List.map acctToChip sceneModel.matches
          , [ vspace (if List.length sceneModel.badNews > 0 then 40 else 0) ]
          , if not (List.isEmpty sceneModel.matches)
             then [audio [src "/static/members/beep-22.mp3", autoplay True] []]
             else [vspace 0]
          ]
        )
    )
    []  -- No buttons
    sceneModel.badNews

-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

sceneChipCss =
  [ css "margin-left" "3px"
  , css "margin-right" "3px"
  ]
