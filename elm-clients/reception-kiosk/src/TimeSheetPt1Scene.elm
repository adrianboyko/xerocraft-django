
module TimeSheetPt1Scene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , TimeSheetPt1Model
  , infoToVerifyStyle -- Used by Pt2 and Pt3
  , pastWorkStyle -- Used by Pt2 and Pt3
  )

-- Standard
import Html exposing (Html, text, div, span, table, tr, td)
import Html.Attributes exposing (style, colspan)
import Http
import Time exposing (Time, hour, minute)
import Tuple

-- Third Party
import Material
import Maybe.Extra as MaybeX
import Update.Extra as UpdateX exposing (addCmd)
import List.Nonempty exposing (Nonempty)

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
  , oldBusinessModel : OldBusinessModel
  , xisSession : XisApi.Session Msg
  }


type alias TimeSheetPt1Model =
  { oldBusinessItem : Maybe OldBusinessItem
  , hrsWorked : Maybe Int
  , minsWorked : Maybe Int
  , badNews : List String
  }


init : Flags -> (TimeSheetPt1Model, Cmd Msg)
init flags =
  let sceneModel =
    { oldBusinessItem = Nothing
    , hrsWorked = Nothing
    , minsWorked = Nothing
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
    selectedItem = kioskModel.oldBusinessModel.selectedItem

  in case (appearing, vanishing, selectedItem) of

    -- This scene assumes that a visit to OldBusiness means that we'll likely be
    -- dealing with a different T/C/W item when we get here. So reset this scene's state.
    (OldBusiness, _, _) ->
      ( { sceneModel
        | oldBusinessItem = Nothing
        , hrsWorked = Nothing
        , minsWorked = Nothing
        }
      , Cmd.none
      )

    (TimeSheetPt1, OldBusiness, Just _) ->
      ( { sceneModel
        | oldBusinessItem = selectedItem
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

    TS1_Submit task claim work ->
      let
        chooseHr = "Must choose an hour value."
        chooseMin = "Must choose a minute value."
      in
        case (sceneModel.hrsWorked, sceneModel.minsWorked) of

          (Nothing, Nothing) ->
            ({sceneModel | badNews=[chooseHr, chooseMin]}, Cmd.none)

          (Nothing, _) ->
            ({sceneModel | badNews=[chooseHr]}, Cmd.none)

          (_, Nothing) ->
            ({sceneModel | badNews=[chooseMin]}, Cmd.none)

          (Just hrs, Just mins) ->
            let
              dur = Time.hour * (toFloat hrs) + Time.minute * (toFloat mins)
              revisedWork = XisApi.setWorksDuration (Just dur) work
            in
              ( { sceneModel
                | oldBusinessItem=Just (OldBusinessItem task claim revisedWork)
                , badNews=[]
                }
              , segueTo TimeSheetPt2
              )

    TS1_HrPad hr ->
      ({sceneModel | hrsWorked=Just hr}, Cmd.none)

    TS1_MinPad mins ->
      ({sceneModel | minsWorked=Just mins}, Cmd.none)


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
    hrButton h =
      td []
        [ padButton kioskModel
           <| PadButtonSpec (h |> toString) (TimeSheetPt1Vector <| TS1_HrPad h)
           <| case sceneModel.hrsWorked of
               Just x -> h==x
               Nothing -> False
        ]
    minButton m =
      td []
        [ padButton kioskModel
           <| PadButtonSpec (m |> toString |> String.padLeft 2 '0') (TimeSheetPt1Vector <| TS1_MinPad m)
           <| case sceneModel.minsWorked of
                Just x -> m==x
                Nothing -> False
        ]
  in
    genericScene kioskModel

      "Volunteer Timesheet"

      "Let us know how long you worked!"

      ( div []
        [ vspace 50
        , div [infoToVerifyStyle]
            [ text ("Task: \"" ++ task.data.shortDesc ++ "\"")
            , vspace 20
            , text ("Date: " ++ dateStr)
            ]
        , if CalendarDate.equal today work.data.workDate then
            vspace 0
          else
            span [pastWorkStyle] [vspace 5, text "(Note: This work was done in the past)"]
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

infoToVerifyStyle = style
  [ "display" => "inline-block"
  , "padding" => px 20
  , "background" => textAreaColor
  , "border-width" => px 1
  , "border-color" => "black"
  --Cou, "border-style" => "solid"
  , "border-radius" => px 10
  ]
