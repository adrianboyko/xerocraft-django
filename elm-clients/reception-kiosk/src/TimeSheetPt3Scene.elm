
module TimeSheetPt3Scene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , TimeSheetPt3Model
  )

-- Standard
import Html exposing (Html, text, div, span)
import Html.Attributes exposing (style)
import Http exposing (header, Error(..))

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
import Duration


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
  , badNews : List String
  }


init : Flags -> (TimeSheetPt3Model, Cmd Msg)
init flags =
  let sceneModel =
    { records = Nothing
    , witnessUsername = ""
    , witnessPassword = ""
    , badNews = []
    }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (TimeSheetPt3Model, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  let
    sceneModel = kioskModel.timeSheetPt3Model
    pt1Model = kioskModel.timeSheetPt1Model
    pt2Model = kioskModel.timeSheetPt2Model
  in
    if appearingScene == TimeSheetPt3 then
      case (pt1Model.taskInProgress, pt1Model.claimInProgress, pt1Model.workInProgress) of

        (Received task, Received (Just claim), Received (Just work)) ->
          let records = Just (task, claim, work)
          in ({sceneModel | records=records}, Cmd.none)

        _ ->
          ({sceneModel | badNews=[tcwMissingMsg]}, Cmd.none)

    else
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

  in case msg of

    TS3_UpdateWitnessUsername s ->
      ({sceneModel | witnessUsername = s}, Cmd.none)

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
            cmd = xis.getMemberList [UsernameEquals wName] (TimeSheetPt3Vector << TS3_WitnessSearchResult)
          in
            (sceneModel, cmd)

    -- Order of updates is important. Update Work here, update Claim later.
    TS3_WitnessSearchResult (Ok {results}) ->
      case sceneModel.records of
        Nothing -> ({sceneModel | badNews=[tcwMissingMsg]}, Cmd.none)
        Just (t, c, w) ->
          case (List.length results) of

            0 ->
              ({sceneModel | badNews=["Could not find "++wName]}, Cmd.none)

            1->
              let
                witnessUrl = Maybe.map (\w -> xis.memberUrl w.id) (List.head results)
                workDur = Maybe.map ((*) Duration.hour) w.workDuration
                workMod = {w | witness=witnessUrl, workDuration=workDur}
                witnessHeader = Http.header "X-Witness-PW" sceneModel.witnessPassword
                cmd = xis.putWorkWithHeaders [witnessHeader] workMod
                  (TimeSheetPt3Vector << TS3_WorkUpdated)
              in
                ({sceneModel | badNews=[]}, cmd)

            _ ->
              ({sceneModel | badNews=["No unique result for "++wName]}, Cmd.none)

    -- Order of updates is important. Update Claim here, now that Work update is done.
    TS3_WorkUpdated (Ok work) ->
      case sceneModel.records of
        Nothing -> ({sceneModel | badNews=[tcwMissingMsg]}, Cmd.none)
        Just (t, c, w) ->
          let
            -- TODO: Task might not be done. Work might be stopping for now.
            claimMod = {c | status=DoneClaimStatus}
            cmd = xis.putClaim claimMod (TimeSheetPt3Vector << TS3_ClaimUpdated)
          in
            ({sceneModel | badNews=[]}, cmd)

    TS3_ClaimUpdated (Ok claim) ->
      (sceneModel, Cmd.none)

    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

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
    dateStr = CalendarDate.format "%a, %b %ddd" work.workDate
    startTime = Maybe.withDefault (ClockTime 0 0) work.workStartTime  -- Should not be Nothing
    startTimeStr = ClockTime.format "%I:%M %P" startTime
    workDur = Maybe.withDefault 0 work.workDuration  -- Should not be Nothing
  in genericScene kioskModel

  "Volunteer Timesheet"

  "A staffer must verify & witness your claim"

    ( div []
      [ vspace 50
      , div [infoToVerifyStyle]
         [ text ("Task: \"" ++ task.shortDesc ++ "\"")
         , vspace 20
         , text (dateStr ++ " @ " ++ startTimeStr ++ " for " ++ (toString workDur) ++ " hrs")
         , if String.length pt2Model.otherWorkDesc > 0
             then div [otherWorkDescStyle] [vspace 20, text pt2Model.otherWorkDesc]
             else text ""
         ]
      , if CalendarDate.equal today work.workDate then
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

    [ ButtonSpec "Verify" (TimeSheetPt3Vector <| TS3_Witnessed) ]

    sceneModel.badNews



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