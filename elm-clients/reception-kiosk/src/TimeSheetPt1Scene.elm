
module TimeSheetPt1Scene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , TimeSheetPt1Model
  )

-- Standard
import Html exposing (Html, text, div, span, table, tr, td)
import Html.Attributes exposing (attribute, style, colspan)
import Http
import Time exposing (Time, hour, minute)
import Tuple

-- Third Party
import Material
import Maybe.Extra as MaybeX
import Update.Extra as UpdateX exposing (addCmd)
import List.Nonempty exposing (Nonempty)

-- Local
import TimeSheetCommon exposing (infoDiv)
import XisRestApi as XisApi exposing (..)
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import DjangoRestFramework as DRF
import PointInTime exposing (PointInTime)
import CalendarDate exposing (CalendarDate)
import ClockTime exposing (ClockTime)
import Duration exposing (Duration)


-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------

idxTimeSheetPt1 = mdlIdBase TimeSheetPt1

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  { a
  ------------------------------------
  | mdl : Material.Model
  , flags : Flags
  , sceneStack : Nonempty Scene
  ------------------------------------
  , currTime : PointInTime
  , timeSheetPt1Model : TimeSheetPt1Model
  , xisSession : XisApi.Session Msg
  }


type alias TimeSheetPt1Model =
  ---------- Req'd Args:
  { tcw : Maybe TaskClaimWork
  ---------- Other State:
  , hrsWorked : Int
  , minsWorked : Int
  , badNews : List String
  }


init : Flags -> (TimeSheetPt1Model, Cmd Msg)
init flags =
  let sceneModel =
    ------------ Req'd Args:
    { tcw = Nothing
    ------------ Other State:
    , hrsWorked = 0
    , minsWorked = 0
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
    selectedItem = sceneModel.tcw

  in case (appearing, vanishing, selectedItem) of

    -- This scene assumes that a visit to OldBusiness means that we'll likely be
    -- dealing with a different T/C/W item when we get here. So reset this scene's state.
    (OldBusiness, _, _) ->
      ( { sceneModel
        | tcw = Nothing
        , hrsWorked = 0
        , minsWorked = 0
        }
      , Cmd.none
      )

    (TimeSheetPt1, OldBusiness, Just _) ->
      ( { sceneModel
        | tcw = selectedItem
        }
      , Cmd.none
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

    TS1_Segue tcw ->
      ( {sceneModel | tcw = Just tcw}
      , send <| WizardVector <| Push <| TimeSheetPt1
      )

    TS1_Submit task claim work ->
      let
        needNonZeroDur = "Specify some hours and/or minutes of work."
        maybeDelete = "If you didn't work, hit BACK and delete this task."
      in
        case (sceneModel.hrsWorked, sceneModel.minsWorked) of

          (0, 0) ->
            ({sceneModel | badNews=[needNonZeroDur, maybeDelete]}, Cmd.none)

          (hrs, mins) ->
            let
              dur = Time.hour * (toFloat hrs) + Time.minute * (toFloat mins)
              revisedWork = XisApi.setWorksDuration (Just dur) work
              tcw = TaskClaimWork task claim revisedWork
            in
              ( { sceneModel | tcw = Just tcw, badNews = []}
              , send <| TimeSheetPt2Vector <| TS2_Segue tcw
              )

    TS1_HrPad hr ->
      ({sceneModel | hrsWorked=hr}, Cmd.none)

    TS1_MinPad mins ->
      ({sceneModel | minsWorked=mins}, Cmd.none)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.timeSheetPt1Model
  in
    case (sceneModel.tcw) of

      Just {task, claim, work} ->
        normalView kioskModel task claim work

      Nothing ->
        errorView kioskModel "Sorry, but something went wrong."


normalView : KioskModel a -> XisApi.Task -> XisApi.Claim -> XisApi.Work -> Html Msg
normalView kioskModel task claim work =
  let
    sceneModel = kioskModel.timeSheetPt1Model
    today = PointInTime.toCalendarDate kioskModel.currTime
    workedToday = CalendarDate.equal today work.data.workDate
    hrButton h =
      td []
        [ padButton kioskModel
           <| PadButtonSpec (h |> toString) (TimeSheetPt1Vector <| TS1_HrPad h)
           <| h == sceneModel.hrsWorked
        ]
    minButton m =
      td []
        [ padButton kioskModel
           <| PadButtonSpec (m |> toString |> String.padLeft 2 '0') (TimeSheetPt1Vector <| TS1_MinPad m)
           <| m == sceneModel.minsWorked
        ]
  in
    genericScene kioskModel

      "Volunteer Timesheet"

      "Let us know how long you worked!"

      ( div []
        [ vspace 50
        , infoDiv kioskModel.currTime task claim work Nothing
        , vspace 60
        , table [padStyle]
          [ tr [padHeaderStyle] [ td [colspan 3] [text "Hours"], td [] [text "&"], td [colspan 3] [text "Minutes"] ]
          , tr [] [ hrButton 0, hrButton 1, hrButton 2, td [] [], minButton 00, minButton 10, minButton 20 ]
          , tr [] [ hrButton 3, hrButton 4, hrButton 5, td [] [], minButton 30, minButton 40, minButton 50 ]
          ]
        , vspace 20
        ]
      )

      [ ButtonSpec "Submit" (TimeSheetPt1Vector <| TS1_Submit task claim work) True]

      sceneModel.badNews


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

padStyle = style
  [ "border-spacing" => px 10
  , "display" => "inline-block"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  ]

padHeaderStyle = style
  [ "height" => px 60
  ]

pastWorkStyle = style
  [ "color" => "red"
  , "font-size" => pt 16
  ]
