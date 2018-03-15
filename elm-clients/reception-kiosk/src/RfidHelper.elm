module RfidHelper exposing
  ( create
  , rfidCharsOnly
  , subscriptions
  , tick
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
import Http
import Time exposing (Time)

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
import DjangoRestFramework as DRF

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


type State
  = Nominal
  | CheckingAnRfid Int
  | EncounteredHttpErr Http.Error
  | FoundRfidToBeGood
  | FoundRfidToBeBad


type alias RfidHelperModel =
  { typed : String
  , rfidsToCheck : List Int
  , isCheckingRfid : Bool
  , loggedAsPresent : Set Int
  , clientsMemberVector : Result String Member -> Msg
  , httpErr : Maybe Http.Error
  , waitCount : Int
  }


create : (Result String Member->Msg) -> RfidHelperModel
create vectorForMember =
  { typed = ""
  , rfidsToCheck = []
  , isCheckingRfid = False
  , loggedAsPresent = Set.empty
  , clientsMemberVector = vectorForMember
  , httpErr = Nothing
  , waitCount = 0
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
              checkAnRfid kioskModel {model | typed=typed, rfidsToCheck=newRfidsToCheck} xis

      RH_MemberListResult (Ok {results}) ->
        case results of

          member :: [] ->  -- Exactly ONE match. Good.
            let
              -- Tell our client that an RFID has been swiped:
              cmd1 = send <| model.clientsMemberVector <| Ok member
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
              cmd3 = popThisScene kioskModel
              newModel =
                { model
                | isCheckingRfid = False
                , rfidsToCheck = []
                , typed = ""
                , loggedAsPresent = Set.insert member.id model.loggedAsPresent
                }
            in
              (newModel, Cmd.batch [cmd1, cmd2, cmd3])

          [] ->  -- ZERO matches. Bad.
            checkAnRfid kioskModel {model | isCheckingRfid=False} xis

          member :: members ->  -- More than one match. Bad.
            checkAnRfid kioskModel {model | isCheckingRfid=False} xis

      RH_MemberPresentResult (Ok _) ->
        -- Don't need to do anything when this succeeds.
        (model, Cmd.none)

      -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

      RH_MemberListResult (Err e) ->
        checkAnRfid kioskModel {model | isCheckingRfid=False, httpErr=Just e} xis

      RH_MemberPresentResult (Err e) ->
          ({model | httpErr=Just e} , Cmd.none)



checkAnRfid : KioskModel a -> RfidHelperModel -> XisApi.Session Msg -> (RfidHelperModel, Cmd Msg)
checkAnRfid kioskModel model xis =
  if model.isCheckingRfid then
    -- We only check one at a time, and a check is already in progress, so do nothing.
    (model, Cmd.none)
  else
    -- We'll check the first one on the list, if it's non-empty.
    case model.rfidsToCheck of

      rfid :: rfids ->
        let
          newModel = {model | rfidsToCheck=rfids, isCheckingRfid=True, waitCount=0}
          memberFilters = [RfidNumberEquals rfid]
          listCmd = xis.listMembers memberFilters (RfidHelperVector << RH_MemberListResult)
          pushCmd = pushThisScene kioskModel
        in
          (newModel, Cmd.batch [listCmd, pushCmd])

      [] ->
        -- There aren't any ids to check. Everything we've tried has failed.
        ({model | isCheckingRfid=False}, Cmd.none)


pushThisScene : KioskModel a -> Cmd Msg
pushThisScene kioskModel =
  if sceneIsVisible kioskModel RfidHelper then
    Cmd.none
  else
    send <| WizardVector <| Push RfidHelper


popThisScene : KioskModel a -> Cmd Msg
popThisScene kioskModel =
  if sceneIsVisible kioskModel RfidHelper then
    send <| WizardVector <| Pop
  else
    Cmd.none


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view  : KioskModel a -> Html Msg
view kioskModel =
  if kioskModel.rfidHelperModel.isCheckingRfid then
    viewCheckingRfid kioskModel
  else
    case kioskModel.rfidHelperModel.httpErr of
      Just e -> viewHttpError kioskModel e
      Nothing -> viewBadRfid kioskModel


viewCheckingRfid : KioskModel a -> Html Msg
viewCheckingRfid kioskModel =
  genericScene kioskModel
    ("Checking Your RFID")
    ""
    (div [sceneTextStyle]
      [ vspace 225
      , text "One moment while we check our database."
      , vspace 20
      , text (String.repeat kioskModel.rfidHelperModel.waitCount "●")
      ]
    )
    []
    []


viewHttpError : KioskModel a -> Http.Error -> Html Msg
viewHttpError kioskModel err =
  let model = kioskModel.rfidHelperModel
  in genericScene kioskModel
    ("Http Problem!")
    (DRF.httpErrToStr err)
    (div [sceneTextStyle]
      [ vspace 225
      , text "Tap the BACK button and try again or"
      , vspace 0
      , text "speak to a staff member for help."
      ]
    )
    []
    []


viewBadRfid : KioskModel a -> Html Msg
viewBadRfid kioskModel =
  let model = kioskModel.rfidHelperModel
  in genericScene kioskModel
    ("RFID Problem")
    ""
    (div [sceneTextStyle]
      [ vspace 225
      , text "Couldn't find your RFID in our database."
      , vspace 0
      , text "Tap the BACK button and try again or"
      , vspace 0
      , text "speak to a staff member for help."
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
-- TICK (called each second)
-----------------------------------------------------------------------------

tick : Time -> KioskModel a -> (RfidHelperModel, Cmd Msg)
tick time kioskModel =
  let
    visible = sceneIsVisible kioskModel RfidHelper
    sceneModel = kioskModel.rfidHelperModel
    inc = if visible && sceneModel.isCheckingRfid then 1 else 0
    newWaitCount = sceneModel.waitCount + inc
  in
    if visible then ({sceneModel | waitCount=newWaitCount}, Cmd.none)
    else (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UTILITY
-----------------------------------------------------------------------------

send : msg -> Cmd msg
send msg =
  Task.succeed msg
  |> Task.perform identity
