
module ReceptionKiosk.VolunteerInScene exposing (init, update, view, VolunteerInModel)

-- Standard
import Html exposing (Html, text, div)
import Html.Attributes exposing (style)
import Http

-- Third Party
import Material.Toggles as Toggles
import Material.Options as Options exposing (css)
import Material.List as Lists

-- Local
import ReceptionKiosk.Types exposing (..)
import ReceptionKiosk.CheckInScene exposing (CheckInModel)
import ReceptionKiosk.SceneUtils exposing (..)
import TaskApi exposing (..)



-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias VolunteerInModel =
  { workableTasks : List OpsTask
  , selectedTask : Maybe OpsTask
  , badNews : List String
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  (SceneUtilModel
    { a
    | volunteerInModel : VolunteerInModel
    , checkInModel : CheckInModel
    }
  )

init : Flags -> (VolunteerInModel, Cmd Msg)
init flags =
  let sceneModel = { workableTasks=[], selectedTask=Nothing, badNews=[] }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : VolunteerInMsg -> KioskModel a -> (VolunteerInModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.volunteerInModel
  in case msg of

    CalendarPageResult (Ok page) ->
      ({sceneModel | workableTasks = page |> extractTodaysTasks |> extractWorkableTasks }, Cmd.none)

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
  if List.isEmpty kioskModel.volunteerInModel.workableTasks then
    noTasksScene kioskModel
  else
    listTasksScene kioskModel

noTasksScene kioskModel =
  genericScene kioskModel
    "You Need a Task!"
    "Please talk to a Staff Member"
    (text "")
    [ButtonSpec "OK" (WizardVector <| Push <| VolunteerInDone)]  -- TODO: Wrong destination


listTasksScene kioskModel =
  genericScene kioskModel
    "Choose a Task"
    "Here are some you can work"
    (taskChoices kioskModel)
    [ButtonSpec "OK" (WizardVector <| Push <| VolunteerInDone)]  -- TODO: Wrong destination

taskChoices : KioskModel a -> Html Msg
taskChoices kioskModel =
  let sceneModel = kioskModel.volunteerInModel
  in div [volunteerInStyle]
    ([vspace 30] ++ List.map
      (\wt ->
        div [taskDivStyle]
          [ Toggles.radio MdlVector [mdlIdBase VolunteerIn + wt.taskId] kioskModel.mdl
            [ Toggles.value
              (case sceneModel.selectedTask of
                Nothing -> False
                Just st -> st == wt
              )
            , Options.onToggle (VolunteerInVector <| ToggleTask <| wt)
            ]
            [text wt.shortDesc]
          ]
      )
      sceneModel.workableTasks
    )


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

volunteerInStyle = style
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
