
module TaskListScene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , TaskListModel
  )

-- Standard
import Html exposing (Html, text, div)
import Html.Attributes exposing (style)
import Http

-- Third Party
import Material.Toggles as Toggles
import Material.Options as Options exposing (css)
import Material.List as Lists

-- Local
import TaskApi exposing (OpsTask, getTodayCalendarPageForMember, CalendarPage)
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import CheckInScene exposing (CheckInModel)


-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------

staffingStatus_STAFFED = "S"  -- As defined in Django backend.
taskPriority_HIGH = "H"  -- As defined in Django backend.

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
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (TaskListModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  case appearingScene of

    ReasonForVisit ->
      -- Start fetching workable tasks b/c they *might* be on their way to this (TaskList) scene.
      let
        cmd = getTodayCalendarPageForMember
          kioskModel.flags.csrfToken
          kioskModel.checkInModel.memberNum
          (TaskListVector << CalendarPageResult)
      in (kioskModel.taskListModel, cmd)

    _ ->
      (kioskModel.taskListModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : TaskListMsg -> KioskModel a -> (TaskListModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.taskListModel

  in case msg of

    CalendarPageResult (Ok page) ->
      let
        workableTasks = page |> extractTodaysTasks |> extractWorkableTasks
        selectedTask = workableTasks |> findStaffedTask
        newSceneModel =
          { sceneModel
          | calendarPageRcvd=True
          , workableTasks=workableTasks
          , selectedTask=selectedTask
          }
      in (newSceneModel, Cmd.none)

    CalendarPageResult (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

    ToggleTask opsTask ->
      ({sceneModel | selectedTask=Just opsTask, badNews=[]}, Cmd.none)

    ValidateTaskChoice ->
      case sceneModel.selectedTask of
        Just task ->
          (sceneModel, segueTo VolunteerInDone)
        Nothing ->
          ({sceneModel | badNews=["You must choose a task to work!"]}, Cmd.none)


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

findStaffedTask : List OpsTask -> Maybe OpsTask
findStaffedTask tasks =
  let
    filter = \t -> t.staffingStatus == staffingStatus_STAFFED
    staffedTasks = List.filter filter tasks
  in
    List.head staffedTasks



-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

idxTaskListScene = mdlIdBase TaskList

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
    [ButtonSpec "OK" (TaskListVector <| ValidateTaskChoice)]
    sceneModel.badNews

taskChoices : KioskModel a -> Html Msg
taskChoices kioskModel =
  let sceneModel = kioskModel.taskListModel
  in div [taskListStyle]
    ([vspace 30] ++ List.indexedMap
      (\index wt ->
        div [taskDivStyle (if wt.priority == taskPriority_HIGH then "#ccffcc" else "#dddddd")]
          [ Toggles.radio MdlVector [idxTaskListScene, index] kioskModel.mdl
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

taskDivStyle color = style
  [ "background-color" => color
  , "padding" => "10px"
  , "margin" => "15px"
  , "border-radius" => "20px"
  ]
