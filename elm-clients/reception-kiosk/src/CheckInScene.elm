
module CheckInScene exposing
  ( init
  , view
  , update
  , tick
  , subscriptions
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

-- TODO: Before user types flexid, could show usernames of recent RFID swipers?
-- TODO: If user is signing in after acct creation, show a username hint?

-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------

maxIdleSeconds = 30


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- REVIEW: Strictly speaking, flexID and memberNum should be Maybes.
type alias CheckInModel =
  { flexId : String  -- UserName or surname.
  , secondsIdle : Int
  , matches : List MembersApi.MatchingAcct  -- Matches to username/surname
  , memberNum : Int -- The member number that the person chose to check in as.
  , doneWithFocus : Bool  -- Only want to set default focus once.
  , badNews : List String
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a = (SceneUtilModel {a | checkInModel : CheckInModel})

init : Flags -> (CheckInModel, Cmd Msg)
init flags =
  let model =
    { flexId = ""  -- A harmless initial value.
    , secondsIdle = 0
    , matches = []
    , memberNum = -99  -- A harmless initial value.
    , doneWithFocus = False
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
          ( {sceneModel | flexId = id, secondsIdle = 0}
          , getMatchingAccts id (CheckInVector << UpdateMatchingAccts)
          )
        else
          ( {sceneModel | matches = [], flexId = id, secondsIdle = 0}
          , Cmd.none
          )

    UpdateMatchingAccts (Ok {target, matches}) ->
      if target == sceneModel.flexId
      then ({sceneModel | matches = matches, badNews = []}, Cmd.none)
      else (sceneModel, Cmd.none)

    UpdateMatchingAccts (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

    UpdateMemberNum memberNum ->
      ({sceneModel | memberNum = memberNum}, segueTo ReasonForVisit)

    FlexIdFocusSet wasSet ->
      let
        currDoneWithFocus = sceneModel.doneWithFocus
        newDoneWithFocus = currDoneWithFocus || wasSet
      in
        ({sceneModel | doneWithFocus = newDoneWithFocus}, Cmd.none)


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
             then [vspace 30, text "Tap your userid, below:", vspace 20]
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
    newSecondsIdle = sceneModel.secondsIdle + inc
    newSceneModel = {sceneModel | secondsIdle = newSecondsIdle}
    setFocusCmd = if sceneModel.doneWithFocus then Cmd.none else idxFlexId |> toString |> setFocusIfNoFocus
    cmd =
       if newSecondsIdle > maxIdleSeconds
         then send (WizardVector <| Reset)
         else setFocusCmd
  in
    if visible then (newSceneModel, cmd)
    else (newSceneModel, Cmd.none)

-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------

subscriptions: KioskModel a -> Sub Msg
subscriptions model =
  if sceneIsVisible model CheckIn
    then focusWasSet (CheckInVector << FlexIdFocusSet)
    else Sub.none


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

sceneChipCss =
  [ css "margin-left" "3px"
  , css "margin-right" "3px"
  ]
