
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
      ({sceneModel | workableTasks = extractTodaysTasks page}, Cmd.none)

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


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  genericScene kioskModel
    "Choose a Task"
    "Here are some you can work"
    (taskChoices kioskModel)
    [ButtonSpec "OK" (WizardVector <| Push <| CheckInDone)]  -- TODO: Wrong destination

taskChoices : KioskModel a -> Html Msg
taskChoices kioskModel =
  let sceneModel = kioskModel.volunteerInModel
  in div [volunteerInStyle]
    ([vspace 30]
    ++
    List.map
      ( \wt ->
        div []
          [ Toggles.radio MdlVector [mdlIdBase VolunteerIn + wt.taskId] kioskModel.mdl
            [ Toggles.value
              (case sceneModel.selectedTask of
                Nothing -> False
                Just st -> st == wt
              )
            , Options.onToggle (VolunteerInVector <| ToggleTask <| wt)
            ]
            [text wt.shortDesc]
          , vspace 30
          ]
      )
      sceneModel.workableTasks
    )


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

volunteerInStyle = style
  [ "width" => "350px"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "padding-left" => "125px"
  , "text-align" => "left"
  ]