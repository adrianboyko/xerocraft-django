module RfidHelper exposing
  ( create
  , rfidCharsOnly
  , subscriptions
  , update
  , view
  , RfidHelperModel
  )

-- Standard
import Regex
import Task as Task
import Char
import Keyboard
import Set exposing (Set)
import Html exposing (Html, div, text, img, br)

-- Third Party
import Material
import List.Nonempty as NonEmpty exposing (Nonempty)
import List.Extra as ListX
import Hex as Hex

-- Local
import Types exposing (..)
import XisRestApi as XisApi exposing (..)
import PointInTime exposing (PointInTime)
import Wizard.SceneUtils exposing (..)


-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------

-- Example of RFID data: ">0C00840D"
-- ">" indicates start of data. It is followed by 8 hex characters.
-- "0C00840D" is the big endian representation of the ID

delimitedRfidNum = Regex.regex ">[0-9A-F]{8}"
rfidCharsOnly = Regex.regex "^[>0-9A-F]*$"


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this module requires.
type alias KioskModel a =
  { a
  ------------------------------------
  | mdl : Material.Model
  , flags : Flags
  , sceneStack : Nonempty Scene
  ------------------------------------
  , rfidHelperModel : RfidHelperModel
  , xisSession : XisApi.Session Msg
  , currTime : PointInTime
  }


type alias RfidHelperModel =
  { typed : String
  , rfidsToCheck : List Int
  , isCheckingRfid : Bool
  , loggedAsPresent : Set Int
  , clientsMemberVector : Result String Member -> Msg
  }


create : (Result String Member->Msg) -> RfidHelperModel
create vectorForMember =
  { typed = ""
  , rfidsToCheck = []
  , isCheckingRfid = False
  , loggedAsPresent = Set.empty
  , clientsMemberVector = vectorForMember
  }


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : RfidHelperMsg -> KioskModel a -> (RfidHelperModel, Cmd Msg)
update msg kioskModel =
    let
      model = kioskModel.rfidHelperModel
      xis = kioskModel.xisSession
    in case msg of

      RH_KeyDown code ->
        let
          typed = case code of
            16 -> model.typed  -- i.e. ignore this shift code.
            190 -> ">"  -- i.e. start char resets the typed buffer.
            c -> model.typed ++ (c |> Char.fromCode |> String.fromChar)
          finds = Regex.find Regex.All delimitedRfidNum typed
        in
          if List.isEmpty finds then
            -- There aren't any delimited rfids
            ({model | typed=typed}, Cmd.none)
          else
            -- There ARE delimited rfids, so pull them out, process them, and pass a modified s through.
            let
              delimitedMatches = List.map .match finds
              hexMatches = List.map (String.dropLeft 1) delimitedMatches
              hexToInt = String.toLower >> Hex.fromString
              resultIntMatches = List.map hexToInt hexMatches
              intMatches = List.filterMap Result.toMaybe resultIntMatches
              newRfidsToCheck = ListX.unique (model.rfidsToCheck++intMatches)
            in
              checkAnRfid {model | typed=typed, rfidsToCheck=newRfidsToCheck} xis

      RH_MemberListResult (Ok {results}) ->
        case results of

          member :: [] ->  -- Exactly ONE match. Good.
            let
              -- Tell our client that an RFID has been swiped:
              cmd1 = send <| model.clientsMemberVector <| Ok (Debug.log "SWIPED" member)
              -- Any time somebody is determined to have swiped their RFID, we'll note that they're present:
              cmd2 =
                if Set.member member.id model.loggedAsPresent then
                  Cmd.none
                else
                  xis.createVisitEvent
                    { who = xis.memberUrl member.id
                    , when = kioskModel.currTime
                    , eventType = VET_Present
                    , method = VEM_FrontDesk
                    , reason = Nothing
                    }
                    (RfidHelperVector << RH_MemberPresentResult)
              newModel =
                { model
                | isCheckingRfid = False
                , rfidsToCheck = []
                , loggedAsPresent = Set.insert member.id model.loggedAsPresent
                }
            in
              (newModel, Cmd.batch [cmd1, cmd2])

          [] ->  -- ZERO matches. Bad.
            checkAnRfid {model | isCheckingRfid=False} xis

          member :: members ->  -- More than one match. Bad.
            checkAnRfid {model | isCheckingRfid=False} xis

      RH_MemberPresentResult (Ok _) ->
        -- Don't need to do anything when this succeeds.
        (model, Cmd.none)

      -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

      RH_MemberListResult (Err error) ->
        checkAnRfid {model | isCheckingRfid=False} xis

      RH_MemberPresentResult (Err e) ->
        let
          _ = Debug.log "RFID ERR" (toString e)
        in
          (model, Cmd.none)



checkAnRfid : RfidHelperModel -> XisApi.Session Msg -> (RfidHelperModel, Cmd Msg)
checkAnRfid model xis =
  if model.isCheckingRfid then
    -- We only check one at a time, and a check is already in progress, so do nothing.
    (model, Cmd.none)
  else
    -- We'll check the first one on the list, if it's non-empty.
    case model.rfidsToCheck of

      rfid :: rfids ->
        let
          newModel = {model | rfidsToCheck=rfids, isCheckingRfid=True}
          memberFilters = [RfidNumberEquals rfid]
          listCmd = xis.listMembers memberFilters (RfidHelperVector << RH_MemberListResult)
        in
          (newModel, listCmd)

      [] ->
        -- There aren't any ids to check. Everything we've tried has failed.
        let
          cmd = send <| WizardVector <| Push RfidHelper
        in
          ({model | isCheckingRfid=False}, cmd)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  genericScene kioskModel
    ("RFID Problem")
    ""
    (div [sceneTextStyle]
      [ vspace 225
      , text "Couldn't find your RFID in our database."
      , vspace 0
      , text "Tap the BACK button and try again or"
      , vspace 0
      , text "speak to a staff member for help."
      , vspace 225
      ]
    )
    []
    []


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------

subscriptions: Sub Msg
subscriptions =
  Keyboard.downs (RfidHelperVector << RH_KeyDown)


-----------------------------------------------------------------------------
-- UTILITY
-----------------------------------------------------------------------------

send : msg -> Cmd msg
send msg =
  Task.succeed msg
  |> Task.perform identity
