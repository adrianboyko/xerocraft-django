
module TimeSheetPt3Scene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , subscriptions
  , TimeSheetPt3Model
  )

-- Standard
import Html exposing (Html, text, div, span)
import Html.Attributes exposing (style)
import Http exposing (header, Error(..))
import Keyboard
import Char

-- Third Party

-- Local
import XisRestApi as XisApi exposing (..)
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import TimeSheetPt1Scene exposing (TimeSheetPt1Model)
import TimeSheetPt2Scene exposing (TimeSheetPt2Model)
import Fetchable exposing (..)
import PointInTime exposing (PointInTime)
import CalendarDate exposing (CalendarDate)
import ClockTime exposing (ClockTime)
import Duration as Dur


-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------

idxTimeSheetPt3 = mdlIdBase TimeSheetPt3
idxWitnessUsername = [idxTimeSheetPt3, 1]
idxWitnessPassword = [idxTimeSheetPt3, 2]

tcwMissingMsg = "Couldn't get task, claim, and work records!"


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  (SceneUtilModel
    { a
    | currTime : PointInTime
    , timeSheetPt1Model : TimeSheetPt1Model
    , timeSheetPt2Model : TimeSheetPt2Model
    , timeSheetPt3Model : TimeSheetPt3Model
    , xisSession : XisApi.Session Msg
    }
  )


type alias TimeSheetPt3Model =
  { records : Maybe (XisApi.Task, XisApi.Claim, XisApi.Work)
  , witnessUsername : String
  , witnessPassword : String
  , digitsTyped : List Char
  , badNews : List String
  }


init : Flags -> (TimeSheetPt3Model, Cmd Msg)
init flags =
  let sceneModel =
    { records = Nothing
    , witnessUsername = ""
    , witnessPassword = ""
    , digitsTyped = []
    , badNews = []
    }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> Scene -> (TimeSheetPt3Model, Cmd Msg)
sceneWillAppear kioskModel appearing vanishing =
  let
    sceneModel = kioskModel.timeSheetPt3Model
    pt1Model = kioskModel.timeSheetPt1Model
  in
    case (appearing, vanishing) of

      (TimeSheetPt3, _) ->
        case (pt1Model.oldBusinessItem) of
          Just {task, claim, work} ->
            let records = Just (task, claim, work)
            in ({sceneModel | records=records}, focusOnIndex idxWitnessUsername)
          _ ->
            ({sceneModel | badNews=[tcwMissingMsg]}, Cmd.none)

      (_, TimeSheetPt3) ->
        -- Clear the password field when we leave this scene.
        ({sceneModel | witnessPassword=""}, Cmd.none)

      (_, _) ->
        (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : TimeSheetPt3Msg -> KioskModel a -> (TimeSheetPt3Model, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.timeSheetPt3Model
    xis = kioskModel.xisSession
    wName = sceneModel.witnessUsername
    amVisible = currentScene kioskModel == TimeSheetPt3

  in case msg of

    -- REVIEW: Factor this out into an RFID reader helper? It's also used in ScreenSaver.
    TS3_KeyDown code ->
      if amVisible then
          case code of
            13 ->
              update TS3_Witnessed kioskModel
            219 ->
              -- RFID reader is beginning to send a card number, so clear our buffer.
              ({sceneModel | digitsTyped=[]}, Cmd.none)
            221 ->
              -- RFID reader is done sending the card number, so process our buffer.
              handleRfid kioskModel
            c ->
              if c>=48 && c<=57 then
                -- A digit, presumably in the RFID's number. '0' = code 48, '9' = code 57.
                let updatedDigits = Char.fromCode c :: sceneModel.digitsTyped
                in ({sceneModel | digitsTyped = updatedDigits }, Cmd.none)
              else
                -- Unexpected code.
                (sceneModel, Cmd.none)
      else
        -- Scene is not visible.
        (sceneModel, Cmd.none)

    TS3_MemberListResult (Ok {results}) ->
      -- ASSERTION: There should be exactly one element in results.
      case List.head results of
        Just witness ->
          ({sceneModel | witnessUsername=witness.data.userName}, Cmd.none)
        Nothing ->
          ({sceneModel | witnessUsername="", badNews=["RFID not registered."]}, Cmd.none)

    TS3_UpdateWitnessUsername s ->
      ({sceneModel | witnessUsername = XisApi.djangoizeId s}, Cmd.none)

    TS3_UpdateWitnessPassword s ->
      ({sceneModel | witnessPassword = s}, Cmd.none)

    TS3_Witnessed ->
      let
        nameIsEmpty = String.isEmpty sceneModel.witnessUsername
        pwIsEmpty = String.isEmpty sceneModel.witnessPassword
      in
        if nameIsEmpty || pwIsEmpty then
          ({sceneModel | badNews = ["Witness name and password must be provided."]}, Cmd.none)
        else
          let
            cmd = xis.listMembers [UsernameEquals wName] (TimeSheetPt3Vector << TS3_WitnessSearchResult)
          in
            (sceneModel, cmd)

    -- Order of updates is important. Update Work here, update Claim later.
    TS3_WitnessSearchResult (Ok {results}) ->
      case sceneModel.records of
        Nothing -> ({sceneModel | badNews=[tcwMissingMsg]}, Cmd.none)
        Just (_, _, w) ->
          case (List.length results) of

            0 ->
              ({sceneModel | badNews=["Could not find "++wName]}, Cmd.none)

            1->
              let
                witnessUrl = Maybe.map (\w -> xis.memberUrl w.id) (List.head results)
                workDur = w.data.workDuration
                workMod = w |> setWorksWitness witnessUrl |> setWorksDuration workDur
                witnessHeader = Http.header "X-Witness-PW" sceneModel.witnessPassword
                cmd = xis.replaceWorkWithHeaders [witnessHeader] workMod
                  (TimeSheetPt3Vector << TS3_WorkUpdated)
              in
                ({sceneModel | badNews=[]}, cmd)

            _ ->
              ({sceneModel | badNews=["No unique result for "++wName]}, Cmd.none)

    -- Order of updates is important. Update Claim here, now that Work update is done.
    TS3_WorkUpdated (Ok work) ->
      case sceneModel.records of
        Nothing -> ({sceneModel | badNews=[tcwMissingMsg]}, Cmd.none)
        Just (_, c, _) ->
          let
            -- TODO: Task might not be done. Work might be stopping for now.
            claimMod = c |> setClaimsStatus DoneClaimStatus
            cmd = xis.replaceClaim claimMod (TimeSheetPt3Vector << TS3_ClaimUpdated)
          in
            ({sceneModel | badNews=[]}, cmd)

    TS3_ClaimUpdated (Ok claim) ->
      case sceneModel.records of
        Nothing -> ({sceneModel | badNews=[tcwMissingMsg]}, Cmd.none)
        Just (_, c, w) ->
          let
            pt2Model = kioskModel.timeSheetPt2Model
            noteData = XisApi.WorkNoteData
              (Just c.data.claimingMember)
              pt2Model.otherWorkDesc
              (xis.workUrl w.id)
              kioskModel.currTime
            cmd = if String.length pt2Model.otherWorkDesc > 0
              then xis.createWorkNote noteData (TimeSheetPt3Vector << TS3_WorkNoteCreated)
              else (popTo OldBusiness)
          in
            ({sceneModel | badNews=[]}, cmd)

    TS3_WorkNoteCreated (Ok note) ->
      -- Everything worked. Scene is complete.
      (sceneModel, popTo OldBusiness)

    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

    TS3_MemberListResult (Err e) ->
      ({sceneModel | badNews=[toString e]}, Cmd.none)

    TS3_WitnessSearchResult (Err e) ->
      ({sceneModel | badNews=[toString e]}, Cmd.none)

    TS3_ClaimUpdated (Err e) ->
      ({sceneModel | badNews=[toString e]}, Cmd.none)

    TS3_WorkUpdated (Err e) ->
      case e of

        BadStatus response ->
          if response.status.code == 403 then
            ({sceneModel | badNews=["Bad username/password?"]}, Cmd.none)
          else
            ({sceneModel | badNews=[toString e]}, Cmd.none)

        _ ->
          ({sceneModel | badNews=[toString e]}, Cmd.none)

    TS3_WorkNoteCreated (Err e) ->
      -- Failure to create the work description is non-critical so we'll carry on to next scene.
      -- TODO: Create a backend logging facility so that failures like this can be noted via XisAPI
      (sceneModel, segueTo TimeSheetPt1)


handleRfid : KioskModel a -> (TimeSheetPt3Model, Cmd Msg)
handleRfid kioskModel =
  let
    sceneModel = kioskModel.timeSheetPt3Model
    rfidNumber = List.reverse sceneModel.digitsTyped |> String.fromList |> String.toInt
    filter = Result.map RfidNumberEquals rfidNumber
    resultHandler = TimeSheetPt3Vector << TS3_MemberListResult
    cmd = case filter of
      Ok f -> kioskModel.xisSession.listMembers [f] resultHandler
      Err err -> Cmd.none
  in
    (sceneModel, cmd)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  case kioskModel.timeSheetPt3Model.records of
    Just (t, c, w) -> viewNormal kioskModel t c w
    _ -> text ""


viewNormal : KioskModel a -> XisApi.Task -> XisApi.Claim -> XisApi.Work -> Html Msg
viewNormal kioskModel task claim work =
  let
    pt2Model = kioskModel.timeSheetPt2Model
    sceneModel = kioskModel.timeSheetPt3Model
    today = PointInTime.toCalendarDate kioskModel.currTime
    dateStr = CalendarDate.format "%a, %b %ddd" work.data.workDate
    workDur = Maybe.withDefault 0 work.data.workDuration  -- Should not be Nothing
  in genericScene kioskModel

  "Volunteer Timesheet"

  "A staffer must verify & witness your claim"

    ( div []
      [ vspace 50
      , div [infoToVerifyStyle]
         [ text ("Task: \"" ++ task.data.shortDesc ++ "\"")
         , vspace 20
         , text ((Dur.toString workDur) ++ " on " ++ dateStr)
         , if String.length pt2Model.otherWorkDesc > 0
             then div [otherWorkDescStyle] [vspace 20, text pt2Model.otherWorkDesc]
             else text ""
         ]
      , if CalendarDate.equal today work.data.workDate then
          vspace 0
        else
          span [pastWorkStyle] [vspace 5, text "(Note: This work was done in the past)"]
      , vspace 70
      , (sceneTextField kioskModel idxWitnessUsername
          "Witness Username" sceneModel.witnessUsername
          (TimeSheetPt3Vector << TS3_UpdateWitnessUsername))
      , vspace 40
      , (scenePasswordField kioskModel idxWitnessPassword
          "Witness Password" sceneModel.witnessPassword
          (TimeSheetPt3Vector << TS3_UpdateWitnessPassword))
      , vspace 20
      ]
    )

    [ ButtonSpec "Verify" (TimeSheetPt3Vector <| TS3_Witnessed) True]

    sceneModel.badNews


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------

subscriptions: KioskModel a -> Sub Msg
subscriptions kioskModel =
    if currentScene kioskModel == TimeSheetPt3 then
      Keyboard.downs (TimeSheetPt3Vector << TS3_KeyDown)
    else
      Sub.none


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

infoToVerifyStyle = style
  [ "display" => "inline-block"
  , "padding" => px 20
  , "background" => textAreaColor
  , "border-width" => px 1
  , "border-color" => "black"
  , "border-style" => "solid"
  , "border-radius" => px 10
  ]

otherWorkDescStyle = style
  [ "width" => px 550
  , "line-height" => "1"
  , "font-size" => pt 20
  ]

pastWorkStyle = style
  [ "color" => "red"
  , "font-size" => pt 16
  ]