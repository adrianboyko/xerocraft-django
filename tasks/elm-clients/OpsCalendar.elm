module OpsCalendar exposing (..)

import Html exposing (..)
import Html.App as Html
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as Dec
import Json.Encode as Enc
import Task
import String
import Time exposing (Time)
import List
import DynamicStyle exposing (hover, hover')

-----------------------------------------------------------------------------
-- UTILITIES
-----------------------------------------------------------------------------

toStr v =
  let
    str = toString v
  in
    if String.left 1 str == "\"" then
      String.dropRight 1 (String.dropLeft 1 str)
    else
      str


-----------------------------------------------------------------------------
-- MAIN
-----------------------------------------------------------------------------

main =
  Html.programWithFlags
    { init = init
    , view = view
    , update = update
    , subscriptions = (\_ -> Sub.none)
    }

-----------------------------------------------------------------------------
-- MODEL
-----------------------------------------------------------------------------

type alias OpsTask =
  { taskId: Int
  , shortDesc: String
  , startTime: Maybe Time
  , endTime: Maybe Time
  , instructions: String
  , staffingStatus: String
  }

type alias DayOfTasks =
  { dayOfMonth: Int
  , isInTargetMonth: Bool  -- REVIEW: Can't this be Bool?
  , isToday: Bool
  , tasks: List OpsTask
  }

type alias WeekOfTasks = List DayOfTasks

type alias MonthOfTasks = List WeekOfTasks

type alias Model =
  { tasks: MonthOfTasks
  , selectedTask: Maybe Int
  , year: Int
  , month: Int
  }

init : Maybe (MonthOfTasks) -> (Model, Cmd Msg)
init monthOfTasks =
  case monthOfTasks of
    Just theTasks ->
      ({tasks=theTasks, selectedTask=Nothing, year=0, month=0}, Cmd.none)
    Nothing ->
      Debug.crash "Parameters MUST be provided by Javascript."

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

type Msg
  = ShowTaskDetail

update : Msg -> Model -> (Model, Cmd Msg)
update action model =
  case action of

    ShowTaskDetail ->
      (model, Cmd.none)


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

unselectable = style
  [ ("-moz-user-select", "-moz-none")
  , ("-khtml-user-select", "none")
  , ("-webkit-user-select", "none")
  , ("-ms-user-select", "none")
  , ("user-select", "none")
  ]

containerStyle = style
  [ ("padding", "0 0")
  , ("width", "100%")
  , ("height", "100%")
  ]

tableStyle = style
  [ ("border-spacing", "0")
  , ("border-collapse", "collapse")
  , ("margin", "0 auto")
  , ("margin-top", "5%")
  , ("display", "table")
  ]

buttonStyle = style
  [ ("font-size", "1.2em")
  , ("margin", "12px 7px") -- vert, horiz
  , ("padding", "7px 13px")
  ]

tdStyle = style
  [ ("border-width", "1px")
  , ("border-color", "black")
  , ("border", "1px solid black")
  , ("padding", "10px")
  , ("vertical-align", "top")
  ]

thStyle = style
  [ ("padding", "5px")
  , ("vertical-align", "top")
  , ("font-family", "Arial, Helvetica")
  , ("font-size", "1.2em")
  ]

dayNumStyle = style
  [ ("font-family", "Arial, Helvetica")
  , ("font-size", "1.25em")
  ]

taskNameCss =
  [ ("font-family", "Roboto Condensed")
  , ("font-size", "0.9em")
  , ("margin", "2px")
  , ("overflow", "hidden")
  , ("white-space", "nowrap")
  , ("text-overflow", "ellipsis")
  , ("width", "120px")
  ]

rollover =
  [ ("background-color", "transparent", "#b3ff99") ]

staffedStyle = hover' (List.concat [[("color", "green")], taskNameCss]) rollover

unstaffedStyle = hover' (List.concat [[("color", "red")], taskNameCss]) rollover

provisionalStyle = hover' (List.concat [[("color", "#c68e17")], taskNameCss]) rollover

dayOtherMonthStyle = style
  [ ("background-color", "#eeeeee")
  ]

dayTargetMonthStyle = style
  [ ("background-color", "white")
  ]

dayTodayStyle = style
  [ ("background-color", "#f0ffff")  -- azure
  ]

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

opsTask : OpsTask -> Html Msg
opsTask ot =
  let
    theStyle = case ot.staffingStatus of
      "S" -> staffedStyle
      "U" -> unstaffedStyle
      "P" -> provisionalStyle
      _   -> Debug.crash "Only S, U, and P are allowed."
  in
     div theStyle [ text ot.shortDesc ]

day : DayOfTasks -> Html Msg
day dayOfTasks =
  let
    monthStyle = case dayOfTasks.isInTargetMonth of
      False -> dayOtherMonthStyle
      True -> dayTargetMonthStyle
    colorStyle = case dayOfTasks.isToday of
      False -> monthStyle
      True -> dayTodayStyle
  in
    td [tdStyle, colorStyle]
      ( List.concat
          [ [span [dayNumStyle] [text (toString dayOfTasks.dayOfMonth)]]
          , List.map opsTask dayOfTasks.tasks
          ]
      )

week : WeekOfTasks -> Html Msg
week weekOfTasks =
  tr []
    (List.map day weekOfTasks)

month : MonthOfTasks -> Html Msg
month monthOfTasks =
  let
    daysOfWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    headify = \x -> (th [thStyle] [text x])
  in
    div [containerStyle]
      [ table [tableStyle, unselectable]
          (List.concat
            [ [tr [] (List.map headify daysOfWeek)]
            , (List.map week monthOfTasks)
            ])
      ]

view : Model -> Html Msg
view model = month model.tasks
