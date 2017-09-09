
module ReceptionKiosk.TaskListScene exposing (init, update, view, TaskListModel)

-- Standard
import Html exposing (Html, text, div)
import Html.Attributes exposing (style)
import Http

-- Third Party
import Material.Toggles as Toggles
import Material.Options as Options exposing (css)
import Material.List as Lists

-- Local
import TaskApi exposing (..)
import Wizard.SceneUtils exposing (..)
import ReceptionKiosk.Types exposing (..)
import ReceptionKiosk.CheckInScene exposing (CheckInModel)



-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias TaskListModel =
  { calendarPageRcvd : Bool  -- There's no guarantee that cal page will be recvd before we get to view func.
  , workableTasks : List OpsTask
  , selectedTask : Maybe OpsTask
  , badNews : List String
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  (SceneUtilModel
    { a
    | taskListModel : TaskListModel
    , checkInModel : CheckInModel
    }
  )

init : Flags -> (TaskListModel, Cmd Msg)
init flags =
  let sceneModel =
    { calendarPageRcvd = False
    , workableTasks = []
    , selectedTask = Nothing
    , badNews = []
    }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : TaskListMsg -> KioskModel a -> (TaskListModel, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.taskListModel
    calPageRcvd = sceneModel.calendarPageRcvd
    noTasks = List.isEmpty sceneModel.workableTasks
  in case msg of

    TaskListSceneWillAppear ->
      if calPageRcvd && noTasks then
        -- No tasks are queued for the member checking in, so skip to task info.
        -- Task info will display generic "talk to a staffer" info in this case.
        (sceneModel, send (WizardVector <| Push <| VolunteerInDone))
      else
        (sceneModel, Cmd.none)

    CalendarPageResult (Ok page) ->
      let workableTasks = page |> extractTodaysTasks |> extractWorkableTasks
      in ({sceneModel | calendarPageRcvd=True, workableTasks=workableTasks }, Cmd.none)

    CalendarPageResult (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

    ToggleTask opsTask ->
      ({sceneModel | selectedTask = Just opsTask}, Cmd.none)


extractTodaysTasks : CalendarPage -> List OpsTask
extractTodaysTasks page =
  let
    extractDayTasks dot = if dot.isToday then dot.tasks else []
    extractWeekTasks wot = List.map extractDayTasks wot |> List.concat
    extractMonthTasks mot = List.map extractWeekTasks mot |> List.concat
  in
    extractMonthTasks page.tasks

extractWorkableTasks : List OpsTask -> List OpsTask
extractWorkableTasks tasks =
  List.filter (\t -> List.length t.possibleActions > 0) tasks

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let sceneModel = kioskModel.taskListModel
  in genericScene kioskModel
    "Choose a Task"
    ( if sceneModel.calendarPageRcvd then
        "Here are some you can work"
      else
        "Looking for tasks. One moment, please!"
    )
    (taskChoices kioskModel)
    [ButtonSpec "OK" (WizardVector <| Push <| VolunteerInDone)]

taskChoices : KioskModel a -> Html Msg
taskChoices kioskModel =
  let sceneModel = kioskModel.taskListModel
  in div [taskListStyle]
    ([vspace 30] ++ List.map
      (\wt ->
        div [taskDivStyle]
          [ Toggles.radio MdlVector [mdlIdBase TaskList + wt.taskId] kioskModel.mdl
            [ Toggles.value
              (case sceneModel.selectedTask of
                Nothing -> False
                Just st -> st == wt
              )
            , Options.onToggle (TaskListVector <| ToggleTask <| wt)
            ]
            [text wt.shortDesc]
          ]
      )
      sceneModel.workableTasks
    )


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

taskListStyle = style
  [ "width" => "500px"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "text-align" => "left"
  ]

taskDivStyle = style
  [ "background-color" => "#eeeeee"
  , "padding" => "10px"
  , "margin" => "10px"
  ]
