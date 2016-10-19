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
  , dayOfMonth: Int
  , shortDesc: String
  , startTime: Maybe Time
  , endTime: Maybe Time
  , instructions: String
  , staffingStatus: String
  }

type alias DayOfTasks = List OpsTask
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
  [ ("text-align", "center")
  , ("padding", "10% 0")
  , ("font-family", "Roboto Condensed, Arial, Helvetica, sans-serif")
  ]

buttonStyle = style
  [ ("font-size", "1.2em")
  , ("margin", "12px 7px") -- vert, horiz
  , ("padding", "7px 13px")
  ]

tableStyle = style
  [ ("border-spacing", "0")
  , ("border-collapse", "collapse")
  , ("margin", "20px 20px 20px 20px")
  ]

tdStyle = style
  [ ("border-width", "1px")
  , ("border-color", "black")
  , ("border", "1px solid black")
  , ("padding", "10px")
  , ("vertical-align", "top")
  ]

taskNameStyle = style
  [ ("font-family", "Arial")
  , ("font-size", "0.8em")
  , ("margin", "2px")
  , ("overflow", "hidden")
  , ("white-space", "nowrap")
  , ("text-overflow", "ellipsis")
  , ("width", "120px")
  ]

dayNumStyle = style
  [ ("font-size", "2em")
  , ("margin", "12px 7px") -- vert, horiz
  , ("padding", "7px 13px")
  ]

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

opsTask : OpsTask -> Html Msg
opsTask ot =
  div [taskNameStyle] [ text ot.shortDesc ]

day : DayOfTasks -> Html Msg
day dayOfTasks =
  td [tdStyle]
    ( List.concat
        [ [ text "2" ]
        , List.map opsTask dayOfTasks
        ]
    )


week : WeekOfTasks -> Html Msg
week weekOfTasks =
  tr []
    (List.map day weekOfTasks)

month : MonthOfTasks -> Html Msg
month monthOfTasks =
  table [tableStyle]
    (List.map week monthOfTasks)

view : Model -> Html Msg
view model = month model.tasks

