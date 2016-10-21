module OpsCalendar exposing (..)

import Html exposing (Html, div, table, tr, td, th, text, span, button, br)
import Html.App as Html
import Html.Attributes exposing (..)
import Html.Events exposing (onClick)
import Http
import Json.Decode as Dec
import Json.Encode as Enc
import Task
import String
import Time exposing (Time)
import List
import Array
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

-- These are params from the server. Elm docs tend to call them "flags".
type alias Flags =
  { tasks: MonthOfTasks
  , year: Int
  , month: Int
  }

type alias Model =
  { tasks: MonthOfTasks
  , year: Int
  , month: Int
  , selectedTask: Maybe Int
  }

init : Maybe (Flags) -> (Model, Cmd Msg)
init flags =
  case flags of
    Just {tasks, year, month} ->
      ({tasks=tasks, year=year, month=month, selectedTask=Nothing}, Cmd.none)
    Nothing ->
      Debug.crash "Parameters MUST be provided by Javascript."

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

type Msg = ShowTaskDetail | PrevMonth | NextMonth

update : Msg -> Model -> (Model, Cmd Msg)
update action model =
  case action of

    ShowTaskDetail ->
      (model, Cmd.none)

    PrevMonth ->
      (model, Cmd.none)

    NextMonth ->
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
  , ("margin-top", "3%")
  , ("width", "100%")
  , ("height", "100%")
  , ("text-align", "center")
  ]

headerStyle = style
  [ ("font-family", "Arial, Helvetica")
  , ("font-size", "2em")
  ]

tableStyle = style
  [ ("border-spacing", "0")
  , ("border-collapse", "collapse")
  , ("margin", "0 auto")
  , ("margin-top", "2%")
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
  , ("text-align", "left")
  ]

thStyle = style
  [ ("padding", "5px")
  , ("vertical-align", "top")
  , ("font-family", "Arial, Helvetica")
  , ("font-size", "1.2em")
  , ("font-weight", "normal")
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
  , ("cursor", "pointer")
  ]

rollover = [ ("background-color", "transparent", "#b3ff99") ]

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

navButtonStyle = style
  [ ("vertical-align", ".28em")
  , ("font-size", "0.6em")
  , ("cursor", "pointer")
  ]

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

taskView : OpsTask -> Html Msg
taskView ot =
  let
    theStyle = case ot.staffingStatus of
      "S" -> staffedStyle
      "U" -> unstaffedStyle
      "P" -> provisionalStyle
      _   -> Debug.crash "Only S, U, and P are allowed."
  in
     div (List.concat [theStyle, [onClick ShowTaskDetail]]) [ text ot.shortDesc ]

dayView : DayOfTasks -> Html Msg
dayView dayOfTasks =
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
          , List.map taskView dayOfTasks.tasks
          ]
      )

weekView : WeekOfTasks -> Html Msg
weekView weekOfTasks =
  tr []
    (List.map dayView weekOfTasks)

monthView : MonthOfTasks -> Html Msg
monthView monthOfTasks =
  let
    daysOfWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    headify = \x -> (th [thStyle] [text x])
  in
     table [tableStyle, unselectable]
       (List.concat
         [ [tr [] (List.map headify daysOfWeek)]
         , (List.map weekView monthOfTasks)
         ])

headerView : Int -> Int -> Html Msg
headerView year month =
  let months = Array.fromList [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"]
  in
    span [headerStyle]
      [ button [navButtonStyle, (onClick PrevMonth)] [text "🠜"]
      , text " "
      , text (Maybe.withDefault "???" (Array.get (month-1) months))
      , text " "
      , text (toStr year)
      , text " "
      , button [navButtonStyle, (onClick NextMonth)] [text "🠞"]
      ]

view : Model -> Html Msg
view model =
  div [containerStyle]
    [ headerView model.year model.month
    , monthView model.tasks
    ]
