module TimeSheetCommon exposing (infoDiv)

-- Standard
import Html exposing (Html, text, div, span)
import Html.Attributes exposing (style)

-- Third Party
import Material as Material
import List.Nonempty as NonEmpty exposing (Nonempty)

-- Local
import Types exposing (..)
import CalendarDate
import Duration
import XisRestApi exposing (Task, Claim, Work, WorkNoteData, Play)
import Wizard.SceneUtils exposing (vspace, px, pt, textAreaColor, (=>), genericScene)
import PointInTime exposing (PointInTime)

-----------------------------------------------------------------------------
-- UTILITIES
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this module requires.
type alias KioskModel a =
  { a
  ------------------------------------
  | mdl : Material.Model
  , flags : Flags
  , sceneStack : Nonempty Scene
  ------------------------------------
  }


-----------------------------------------------------------------------------
-- UTILITIES
-----------------------------------------------------------------------------

infoDiv : PointInTime -> Business -> Maybe String -> Html Msg
infoDiv curr business workDescStr =
  case business of
    SomeTCW {task, claim, work} -> infoDivForTCW curr task claim work workDescStr
    SomePlay play -> infoDivForPlay curr play


infoDivForTCW : PointInTime -> Task -> Claim -> Work -> Maybe String -> Html Msg
infoDivForTCW curr task claim work otherWorkDesc =
  let
    today = PointInTime.toCalendarDate curr
    dateStr = CalendarDate.format "%a, %b %ddd" work.data.workDate
    dateColor = if CalendarDate.equal today work.data.workDate then "black" else "red"
    workDurStr =  case work.data.workDuration of
      Nothing -> ""
      Just dur -> Duration.toString dur ++ " on "
  in
    div [infoToVerifyStyle]
      [ text ("\"" ++ task.data.shortDesc ++ "\"")
      , vspace 20
      , text workDurStr
      , span [style ["color"=>dateColor]] [text dateStr]
        , case otherWorkDesc of
            Just owd ->
              div [otherWorkDescStyle] [vspace 20, text owd]
            Nothing ->
              text ""

      ]

infoDivForPlay : PointInTime -> Play -> Html Msg
infoDivForPlay curr play =
  let
    today = PointInTime.toCalendarDate curr
    dateStr = CalendarDate.format "%a, %b %ddd" play.data.playDate
    dateColor = if CalendarDate.equal today play.data.playDate then "black" else "red"
    playDurStr =  case play.data.playDuration of
      Nothing -> ""
      Just dur -> Duration.toString dur ++ " on "
  in
    div [infoToVerifyStyle]
      [ text ("Membership Privileges")
      , vspace 20
      , text playDurStr
      , span [style ["color"=>dateColor]] [text dateStr]
      ]


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

infoToVerifyStyle = style
  [ "display" => "inline-block"
  , "padding" => px 20
  , "background" => textAreaColor
  , "border-width" => px 1
  , "border-color" => "black"
  --"border-style" => "solid"
  , "border-radius" => px 10
  , "width" => px 500
  ]

otherWorkDescStyle = style
  [ "line-height" => "1"
  , "font-size" => pt 20
  ]
