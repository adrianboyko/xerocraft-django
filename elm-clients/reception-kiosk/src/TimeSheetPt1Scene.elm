
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
import Tuple

-- Third Party
import Maybe.Extra as MaybeX
import Update.Extra as UpdateX exposing (addCmd)
import List.Nonempty as Nonempty

-- Local
import XisRestApi as XisApi exposing (..)
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import DjangoRestFramework as DRF

import PointInTime exposing (PointInTime)
import CalendarDate exposing (CalendarDate)
import ClockTime exposing (ClockTime)
import Duration exposing (Duration)
import OldBusinessScene exposing (OldBusinessModel, OldBusinessItem)


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
    , oldBusinessModel : OldBusinessModel
    , xisSession : XisApi.Session Msg
    }
  )


type alias TimeSheetPt1Model =
  { oldBusinessItem : Maybe OldBusinessItem
  , workStartScratch : String
  , workDurationScratch : String
  , badNews : List String
  }


init : Flags -> (TimeSheetPt1Model, Cmd Msg)
init flags =
  let sceneModel =
    { oldBusinessItem = Nothing
    , workStartScratch = ""
    , workDurationScratch = ""
    , badNews = []
    }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> Scene -> (TimeSheetPt1Model, Cmd Msg)
sceneWillAppear kioskModel appearing vanishing =
  let
    sceneModel = kioskModel.timeSheetPt1Model
    oldBusinessItem = kioskModel.oldBusinessModel.selectedItem

  in case (appearing, vanishing, oldBusinessItem) of

    (TimeSheetPt1, _, Just {task, claim, work}) ->
      let
        workDur = Maybe.withDefault 0 work.data.workDuration  -- I expect workDuration to be Nothing, here.
        durScratch = workDur |> Time.inHours |> toString
        startCT = Maybe.withDefault (ClockTime 19 0) work.data.workStartTime  -- TODO: Bad default.
        startScratch = ClockTime.format "%I:%M %P" startCT
      in
        ( { sceneModel
          | oldBusinessItem = oldBusinessItem
          , workDurationScratch = durScratch
          , workStartScratch = startScratch
          }
        , focusOnIndex idxWorkStart
        )


    (TimeSheetPt1, _, Nothing) ->
      -- TODO: This is a bad error. Segue to Check[In|Out]Done? Segue to error page?
      (sceneModel, Cmd.none)

    (_, _, _) ->
      (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : TimeSheetPt1Msg -> KioskModel a -> (TimeSheetPt1Model, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.timeSheetPt1Model
    xis = kioskModel.xisSession

  in case msg of

    TS1_Submit task claim work ->
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
              revisedWork = {work | data = newData}
              cmd = segueTo TimeSheetPt2
            in
              ( { sceneModel
                | oldBusinessItem=Just (OldBusinessItem task claim revisedWork)
                , badNews=[]
                }
              , cmd
              )

          (Err e1, Err e2) -> ({sceneModel | badNews=[e1, e2]}, Cmd.none)
          (Err e, _) -> ({sceneModel | badNews=[e]}, Cmd.none)
          (_, Err e) -> ({sceneModel | badNews=[e]}, Cmd.none)

    TS1_UpdateTimeStarted s ->
      ({sceneModel | workStartScratch = String.toUpper s}, Cmd.none)

    TS1_UpdateDuration s ->
      ({sceneModel | workDurationScratch = s}, Cmd.none)



-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.timeSheetPt1Model
  in
    case (sceneModel.oldBusinessItem) of

      Just {task, claim, work} ->
        normalView kioskModel task claim work

      Nothing ->
        failedView kioskModel "Sorry, but something went wrong."


normalView : KioskModel a -> XisApi.Task -> XisApi.Claim -> XisApi.Work -> Html Msg
normalView kioskModel task claim work =
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

      [ ButtonSpec "Submit" (TimeSheetPt1Vector <| TS1_Submit task claim work) True]

      sceneModel.badNews

failedView : KioskModel a -> String -> Html Msg
failedView kioskModel error =
  let
    sceneModel = kioskModel.timeSheetPt1Model
  in
    genericScene kioskModel
      "Volunteer Timesheet"
      "ERROR"
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
