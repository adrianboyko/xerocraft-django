
module ReceptionKiosk.VolunteerInScene exposing (init, update, view, VolunteerInModel)

-- Standard
import Html exposing (Html, text)
import Http
import List.Extra

-- Third Party
import Material.Toggles as Toggles
import Material.Options as Options exposing (css)
import Material.List as Lists

-- Local
import ReceptionKiosk.Types exposing (..)
import ReceptionKiosk.SceneUtils exposing (..)
import ReceptionKiosk.Backend as Backend
import ReceptionKiosk.CheckInScene exposing (CheckInModel)
import TaskApi exposing (..)

import TaskApi as TaskApi

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

    VolunteerInSceneWillAppear ->
      let request = getCurrCalendarPage (VolunteerInVector << CalendarPageResult)
      in (sceneModel, request)

    CalendarPageResult (Ok page) ->
      ({sceneModel | workableTasks = extractTodaysTasks page}, Cmd.none)

    CalendarPageResult (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

    ToggleTask opsTask ->
--      let
--        replace = List.Extra.replaceIf
--        picker = \x -> x.id == dm.id
--        newDm = { dm | selected = not dm.selected }
--      in
--        -- TODO: This should also add/remove the discovery method choice on the backend.
--        ({sceneModel | discoveryMethods = replace picker newDm sceneModel.discoveryMethods}, Cmd.none)
        (sceneModel, Cmd.none)



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
  in Lists.ul volunteerInCss
    (List.map
      ( \wt ->
          Lists.li [css "font-size" "18pt"]
            [ Lists.content [] [ text wt.shortDesc ]
            , Lists.content2 []
              [ Toggles.checkbox MdlVector [2000+wt.taskId] kioskModel.mdl  -- 2000 establishes an id range for these.
                  [ Toggles.value
                      (case sceneModel.selectedTask of
                        Nothing -> False
                        Just st -> st == wt
                      )
                  , Options.onToggle (VolunteerInVector <| ToggleTask <| wt)
                  ]
                  []
              ]
            ]
      )
      sceneModel.workableTasks
    )


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

volunteerInCss =
  [ css "width" "400px"
  , css "margin-left" "auto"
  , css "margin-right" "auto"
  , css "margin-top" "80px"
  ]
