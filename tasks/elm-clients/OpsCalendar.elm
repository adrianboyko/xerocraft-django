module OpsCalendar exposing (..)

import Html exposing (Html, div, table, tr, td, th, text, span, button, br, p)
import Html.App as Html
import Html.Attributes exposing (..)
import Html.Events exposing (onClick)
import Http
import Task
import String
import Time exposing (Time)
import List
import Array
import DynamicStyle exposing (hover, hover')


import Json.Decode exposing((:=), maybe)
import Json.Decode as Dec
-- elm-package install --yes elm-community/elm-json-extra
import Json.Decode.Extra exposing ((|:))
-- elm-package install -- yes NoRedInk/elm-decode-pipeline
-- import Json.Decode.Pipeline

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

monthName : Int -> String
monthName x =
  case x of
    0 -> "January"
    1 -> "February"
    2 -> "March"
    3 -> "April"
    4 -> "May"
    5 -> "June"
    6 -> "July"
    7 -> "August"
    8 -> "September"
    9 -> "October"
    10 -> "November"
    11 -> "December"
    _ -> Debug.crash "Provide a value from 0 to 11, inclusive"

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
  , isInTargetMonth: Bool
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
  , selectedTaskId: Maybe Int
  , index: List OpsTask
  , working: Bool
  }

init : Flags -> (Model, Cmd Msg)
init {tasks, year, month} =
  (Model tasks year month Nothing (indexMonth tasks) False, Cmd.none)

-----------------------------------------------------------------------------
-- Index tasks by ID
-----------------------------------------------------------------------------

indexMonth : MonthOfTasks -> List OpsTask
indexMonth monthOfTasks =
  List.concat (List.map indexWeek monthOfTasks)

indexWeek : WeekOfTasks -> List OpsTask
indexWeek weekOfTasks =
  List.concat (List.map indexDay weekOfTasks)

indexDay : DayOfTasks -> List OpsTask
indexDay dayOfTasks =
  dayOfTasks.tasks

-----------------------------------------------------------------------------
-- JSON Decoder
-----------------------------------------------------------------------------

decodeOpsTask : Dec.Decoder OpsTask
decodeOpsTask =
  Dec.succeed OpsTask
    |: ("taskId"           := Dec.int)
    |: ("shortDesc"        := Dec.string)
    |: (maybe ("startTime" := Dec.float))
    |: (maybe ("endTime"   := Dec.float))
    |: ("instructions"     := Dec.string)
    |: ("staffingStatus"   := Dec.string)


decodeDayOfTasks : Dec.Decoder DayOfTasks
decodeDayOfTasks =
  Dec.succeed DayOfTasks
    |: ("dayOfMonth"      := Dec.int)
    |: ("isInTargetMonth" := Dec.bool)
    |: ("isToday"         := Dec.bool)
    |: ("tasks"           := Dec.list decodeOpsTask)


decodeFlags : Dec.Decoder Flags
decodeFlags =
  Dec.succeed Flags
    |: ("tasks" := Dec.list (Dec.list decodeDayOfTasks))
    |: ("year"  := Dec.int)
    |: ("month" := Dec.int)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

type Msg
  = ToggleTaskDetail Int
  | HideTaskDetail
  | ClaimTask Int
  | PrevMonth
  | NextMonth
  | NewMonthSuccess Flags
  | NewMonthFailure Http.Error


update : Msg -> Model -> (Model, Cmd Msg)
update action model =
  case action of

    ToggleTaskDetail clickedTaskId ->
      case model.selectedTaskId of
        Nothing -> ({model | selectedTaskId = Just clickedTaskId}, Cmd.none)
        Just selectedTaskId' ->
          if selectedTaskId' == clickedTaskId
            then ({model | selectedTaskId = Nothing}, Cmd.none)
            else ({model | selectedTaskId = Just clickedTaskId}, Cmd.none)

    HideTaskDetail ->
      ({model | selectedTaskId = Nothing}, Cmd.none)

    ClaimTask taskId ->
      (model, Cmd.none)  -- TODO

    PrevMonth ->
      ({model | working = True}, getNewMonth model (-))

    NextMonth ->
      ({model | working = True}, getNewMonth model (+))

    NewMonthSuccess flags ->
      init flags

    NewMonthFailure err ->
      -- TODO: Display some sort of error message.
      case err of
        Http.Timeout -> (model, Cmd.none)
        Http.NetworkError -> (model, Cmd.none)
        Http.UnexpectedPayload _ -> (model, Cmd.none)
        Http.BadResponse _ _ -> (model, Cmd.none)

getNewMonth : Model -> (Int -> Int -> Int) -> Cmd Msg
getNewMonth model op =
  let
    -- TODO: These should be passed in from Django, not hard-coded here.
    url = "/tasks/ops-calendar-json/" ++ toStr(year) ++ "-" ++ toStr(month) ++ "/"
    opMonth = op model.month 1
    year = case opMonth of
      13 -> model.year + 1
      0 -> model.year - 1
      _ -> model.year
    month = case opMonth of
      13 -> 1
      0 -> 12
      _ -> opMonth
  in
    Task.perform
      NewMonthFailure
      NewMonthSuccess
      (Http.get decodeFlags url)


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
     div (List.concat [theStyle, [onClick (ToggleTaskDetail ot.taskId)]]) [ text ot.shortDesc ]

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

headerView : Model -> Html Msg
headerView model =
  span [headerStyle]
    (
    if model.working then
      [ text "Working" ]
    else
      [ button [navButtonStyle, (onClick PrevMonth)] [text "🠜"]
      , text " "
      , text (monthName (model.month-1))
      , text " "
      , text (toStr model.year)
      , text " "
      , button [navButtonStyle, (onClick NextMonth)] [text "🠞"]
      ]
    )

detailView : Model -> Html Msg
detailView model =
  case model.selectedTaskId of
      Nothing -> text ""
      Just selectedTaskId ->
        let
          task' = List.head (List.filter (\t -> t.taskId == selectedTaskId) model.index)
        in
          case task' of
            Nothing -> Debug.crash "Selected task does not appear in index!"
            Just task ->
              div [taskDetailStyle]
                [ p [] [text ("Task ID: "++(toStr selectedTaskId))]
                , p [] [text task.shortDesc]
                , p [] [text task.instructions]
                , button [detailButtonStyle, (onClick HideTaskDetail)] [text "Close"]
                , if task.staffingStatus == "U"
                    then button [detailButtonStyle, (onClick (ClaimTask task.taskId))] [text "Claim"]
                    else text ""
                ]

view : Model -> Html Msg
view model =
  div [containerStyle]
    [ headerView model
    , monthView model.tasks
    , detailView model
    ]

-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

taskDetailStyle = style
  [ ("float", "left")
  , ("width", "400px")
  , ("background-color", "#f0f0f0")
  , ("position", "absolute")
  , ("left", "100px")
  , ("top", "100px")
  , ("text-align", "left")
  , ("padding", "30px")
  ]

unselectable = style
  [ ("-moz-user-select", "-moz-none")
  , ("-khtml-user-select", "none")
  , ("-webkit-user-select", "none")
  , ("-ms-user-select", "none")
  , ("user-select", "none")
  ]

containerStyle = style
  [ ("padding", "0 0")
  , ("padding-top", "3%")
  , ("margin-top", "0")
  , ("width", "100%")
  , ("height", "100%")
  , ("text-align", "center")
  , ("font-family", "Roboto Condensed, Arial, Helvetica")
  , ("font-size", "1em")
  ]

headerStyle = style
  [ ("font-family", "Roboto Condensed, Arial, Helvetica")
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
  [ ("font-family", "Roboto Condensed")
  , ("vertical-align", ".28em")
  , ("font-size", "0.6em")
  , ("cursor", "pointer")
  ]

detailButtonStyle = style
  [ ("font-family", "Roboto Condensed")
  , ("font-size", "1.2em")
  , ("cursor", "pointer")
  , ("margin-right", "10px")
  ]
