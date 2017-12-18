
module TimeSheetPt1Scene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , TimeSheetPt1Model
  )

-- Standard
import Html exposing (Html, text, div, span)
import Html.Attributes exposing (style)
import Http
import Time exposing (Time, hour, minute)

-- Third Party
import Maybe.Extra as MaybeX

-- Local
import XisRestApi as XisApi exposing (..)
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import CheckOutScene exposing (CheckOutModel)
import Fetchable exposing (..)
import DjangoRestFramework as DRF

import PointInTime exposing (PointInTime)
import CalendarDate exposing (CalendarDate)
import ClockTime exposing (ClockTime)
import Duration exposing (Duration)


-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------

idxTimeSheetPt1 = mdlIdBase TimeSheetPt1
idxWorkStart = [idxTimeSheetPt1, 1]
idxWorkDuration = [idxTimeSheetPt1, 2]

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  (SceneUtilModel
    { a
    | currTime : PointInTime
    , timeSheetPt1Model : TimeSheetPt1Model
    , checkOutModel : CheckOutModel
    , xisSession : XisApi.Session Msg
    }
  )


type alias TimeSheetPt1Model = -- This scene first searches for claims in progress.
  { claimInProgress : Fetchable (Maybe XisApi.Claim)  -- They might not have a claim in progress.
  , taskInProgress : Fetchable XisApi.Task  -- But if they do, EVERY claim points to a task.
  , workInProgress : Fetchable (Maybe XisApi.Work)  -- But there might not be a w.i.p. pointing to the claim.
  , workStartScratch : String
  , workDurationScratch : String
  , search : Bool  -- Prevents refetching/reset of task info when user navigates "BACK" button.
  , badNews : List String
  }


init : Flags -> (TimeSheetPt1Model, Cmd Msg)
init flags =
  let sceneModel =
    { claimInProgress = Pending
    , taskInProgress = Pending
    , workInProgress = Pending
    , workStartScratch = ""
    , workDurationScratch = ""
    , search = True  -- Should find a new task the 1st time user arrives at this scene.
    , badNews = []
    }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (TimeSheetPt1Model, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  let
    sceneModel = kioskModel.timeSheetPt1Model
    focusCmd = focusOnIndex idxWorkStart
  in case appearingScene of

    TimeSheetPt1 ->
      -- This scene will only look up info if:
      --   1) The user is arriving at it for the first time.
      --   2) Another scene has set "search" to True.
      if not sceneModel.search then
        (sceneModel, focusCmd)
      else
        let
          memberNum = kioskModel.checkOutModel.checkedOutMemberNum
          cmd = kioskModel.xisSession.listClaims
            [ ClaimingMemberEquals memberNum
            , ClaimStatusEquals WorkingClaimStatus
            ]
            (TimeSheetPt1Vector << TS1_WorkingClaimsResult)
        in
          ({sceneModel | taskInProgress = Pending}, Cmd.batch [cmd, focusCmd])

    _ ->
      (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : TimeSheetPt1Msg -> KioskModel a -> (TimeSheetPt1Model, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.timeSheetPt1Model
    memberNum = kioskModel.checkOutModel.checkedOutMemberNum
    xis = kioskModel.xisSession

  in case msg of

    TS1_WorkingClaimsResult (Ok {results}) ->
      let
        firstClaim = List.head results
        cmd = case firstClaim of
          Nothing ->
            segueTo CheckOutDone
          Just c ->
            Cmd.batch
              [ xis.getTaskFromUrl
                  c.data.claimedTask
                  (TimeSheetPt1Vector << TS1_WorkingTaskResult)
              , xis.listWorks
                  [WorkedClaimEquals c.id, WorkDurationIsNull True]
                  (TimeSheetPt1Vector << TS1_WipResult)
              ]
      in
        ({sceneModel | claimInProgress = Received firstClaim}, cmd)

    TS1_WorkingTaskResult (Ok task) ->
      ({sceneModel | taskInProgress = Received task}, Cmd.none)

    TS1_WipResult (Ok {results}) ->
      case List.head results of
        Nothing -> ({sceneModel | workInProgress = Failed "Work record is missing!" }, Cmd.none)
        Just work ->
          let
            workDur = Maybe.withDefault 0 work.data.workDuration
            durScratch = workDur |> Time.inHours |> toString
            revisedWork = work |> setWorkDuration (Just workDur)
            startCT = Maybe.withDefault (ClockTime 19 0) work.data.workStartTime
            startScratch = ClockTime.format "%I:%M %P" startCT
          in
            ( { sceneModel
              | workInProgress = Received (Just revisedWork)
              , workDurationScratch = durScratch
              , workStartScratch = startScratch
              }
            , Cmd.none
            )

    TS1_Submit claim work ->
      let
        startCT = ClockTime.fromString sceneModel.workStartScratch
        workDur = Duration.fromString sceneModel.workDurationScratch
      in
        case (startCT, workDur) of

          (_, Ok 0) ->
            ({sceneModel | badNews=["Must specify non-zero work time."]}, Cmd.none)

          (Ok ct, Ok dur) ->
            let
              wd = work.data
              newData = {wd | workStartTime=Just ct, workDuration=Just dur}
              revisedWIP = {work | data = newData}
              cmd = segueTo TimeSheetPt2
            in
              ({sceneModel | search=False, workInProgress=Received (Just revisedWIP), badNews=[]}, cmd)

          (Err e1, Err e2) -> ({sceneModel | badNews=[e1, e2]}, Cmd.none)
          (Err e, _) -> ({sceneModel | badNews=[e]}, Cmd.none)
          (_, Err e) -> ({sceneModel | badNews=[e]}, Cmd.none)

    TS1_UpdateTimeStarted s ->
      ({sceneModel | workStartScratch = String.toUpper s}, Cmd.none)

    TS1_UpdateDuration s ->
      ({sceneModel | workDurationScratch = s}, Cmd.none)

    -- -- -- -- ERROR HANDLERS -- -- -- --

    TS1_WorkingClaimsResult (Err error) ->
      ({sceneModel | claimInProgress = Failed (toString error)}, Cmd.none)

    TS1_WorkingTaskResult (Err error) ->
      ({sceneModel | taskInProgress = Failed (toString error)}, Cmd.none)

    TS1_WipResult (Err error) ->
      ({sceneModel | workInProgress = Failed (toString error)}, Cmd.none)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.timeSheetPt1Model
  in
    case (sceneModel.taskInProgress, sceneModel.claimInProgress, sceneModel.workInProgress) of

    (Received task, Received (Just claim), Received (Just work)) ->
      receivedAll kioskModel task claim work

    (Failed err, _, _) -> failedView kioskModel err
    (_, Failed err, _) -> failedView kioskModel err
    (_, _, Failed err) -> failedView kioskModel err

    _ -> pendingView kioskModel


pendingView : KioskModel a -> Html Msg
pendingView kioskModel =
  genericScene kioskModel
    "Volunteer Timesheet"
    "One Moment, Please!"
    ( div []
      [ vspace 40
      , text "Looking up task info..."
      ]
    )
    [] -- no buttons
    [] -- no errors



receivedAll : KioskModel a -> XisApi.Task -> XisApi.Claim -> XisApi.Work -> Html Msg
receivedAll kioskModel task claim work =
  let
    sceneModel = kioskModel.timeSheetPt1Model
    dateStr = CalendarDate.format "%a, %b %ddd" work.data.workDate
    today = PointInTime.toCalendarDate kioskModel.currTime

  in
    genericScene kioskModel

      "Volunteer Timesheet"

      "Let us know how long you worked!"

      ( div []
        [ vspace 40
        , text ("Task: \"" ++ task.data.shortDesc ++ "\"")
        , vspace 20
        , text ("Date: " ++ dateStr)
        , if CalendarDate.equal today work.data.workDate then
            vspace 0
          else
            span [pastWorkStyle] [vspace 5, text "(Note: This work was done in the past)"]
        , vspace 70
        , (sceneTextField kioskModel idxWorkStart
            "Work Started At" sceneModel.workStartScratch
            (TimeSheetPt1Vector << TS1_UpdateTimeStarted))
        , vspace 40
        , (sceneTextField kioskModel idxWorkDuration
            "Hours Worked" sceneModel.workDurationScratch
            (TimeSheetPt1Vector << TS1_UpdateDuration))
        , vspace 20
        ]
      )

      [ ButtonSpec "Submit" (TimeSheetPt1Vector <| TS1_Submit claim work) ]

      sceneModel.badNews

failedView : KioskModel a -> String -> Html Msg
failedView kioskModel error =
  let
    sceneModel = kioskModel.timeSheetPt1Model
  in
    genericScene kioskModel
      "Record Your Volunteer Time"
      ""
      (text "")
      [] -- no buttons
      [error]

-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

pastWorkStyle = style
  [ "color" => "red"
  , "font-size" => pt 16
  ]
