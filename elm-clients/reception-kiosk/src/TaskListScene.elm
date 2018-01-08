
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
import Date
import Time exposing (Time)

-- Third Party
import Material.Toggles as Toggles
import Material.Options as Options exposing (css)
import Material.List as Lists
import Maybe.Extra as MaybeX exposing (isNothing)
import List.Extra as ListX

-- Local
import XisRestApi as XisApi exposing (..)
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import CheckInScene exposing (CheckInModel)
import Fetchable exposing (..)
import DjangoRestFramework as DRF
import PointInTime exposing (PointInTime)


-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------

staffingStatus_STAFFED = "S"  -- As defined in Django backend.
taskPriority_HIGH = "H"  -- As defined in Django backend.

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  (SceneUtilModel
    { a
    | currTime : Time
    , taskListModel : TaskListModel
    , checkInModel : CheckInModel
    , xisSession : XisApi.Session Msg
    }
  )

type alias TaskListModel =
  { workableTasks : Fetchable (List XisApi.Task)
  , selectedTask : Maybe XisApi.Task
  , badNews : List String
  }

init : Flags -> (TaskListModel, Cmd Msg)
init flags =
  let sceneModel =
    { workableTasks = Pending
    , selectedTask = Nothing
    , badNews = []
    }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> Scene -> (TaskListModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene vanishingScene =
  case (appearingScene, vanishingScene) of

    (ReasonForVisit, _) ->
      -- Start fetching workable tasks b/c they *might* be on their way to this (TaskList) scene.
      getWorkableTasks kioskModel

    (TaskList, TaskInfo) ->
      -- User hit back button. Since workable task data was changed by prev visit to this scene, we need to reget it.
      getWorkableTasks kioskModel

    _ ->
      (kioskModel.taskListModel, Cmd.none)

getWorkableTasks : KioskModel a -> (TaskListModel, Cmd Msg)
getWorkableTasks kioskModel =
  let
    sceneModel = kioskModel.taskListModel
    currDate = PointInTime.toCalendarDate kioskModel.currTime
    cmd = kioskModel.xisSession.listTasks
      [ScheduledDateEquals currDate]
      (TaskListVector << TL_TaskListResult)
  in
    ({sceneModel | workableTasks=Pending}, cmd)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : TaskListMsg -> KioskModel a -> (TaskListModel, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.taskListModel
    flags = kioskModel.flags
    memberNum = kioskModel.checkInModel.memberNum
    xis = kioskModel.xisSession

  in case msg of

    TL_TaskListResult (Ok {results, next}) ->
      -- TODO: Deal with the possibility of paged results (i.e. next is not Nothing)?
      let
        -- "Other Work" is offered to everybody, whether or not they are explicitly eligible to work it:
        otherWorkTaskTest task = task.data.shortDesc == "Other Work"
        otherWorkTask = List.filter otherWorkTaskTest results

        -- The more normal case is to offer up tasks that the user can claim:
        memberCanClaimTest = xis.memberCanClaimTask memberNum
        claimableTasks = List.filter memberCanClaimTest results

        -- The offered/workable tasks are the union of claimable tasks and the "Other Work" task.
        workableTasks = claimableTasks ++ otherWorkTask

        -- We also want ot know which task(s) (if any) have already been claimed:
        isCurrentClaimant = xis.memberHasStatusOnTask memberNum CurrentClaimStatus
        claimedTask = ListX.find isCurrentClaimant results
      in
        ( { sceneModel
          | workableTasks = Received workableTasks
          , selectedTask = claimedTask
          }
          , Cmd.none
        )

    TL_ToggleTask toggledTask ->
      let
        claimOnTask = xis.membersClaimOnTask memberNum toggledTask
      in
        ( { sceneModel
          | selectedTask = Just toggledTask
          , badNews = []
          }
        , Cmd.none
      )

    TL_ValidateTaskChoice ->
      case sceneModel.selectedTask of
        Just task ->
          let
            result2Msg = TaskListVector << TL_ClaimUpsertResult
            existingClaim = xis.membersClaimOnTask memberNum task
            upsertCmd = case existingClaim of

              Just c ->
                let
                  claimMod = c |> setClaimsStatus WorkingClaimStatus
                in
                  xis.replaceClaim claimMod result2Msg

              Nothing ->
                xis.createClaim
                  ( ClaimData
                      (Maybe.withDefault 0.0 task.data.workDuration)
                      (Just <| PointInTime.toClockTime kioskModel.currTime)
                      (xis.taskUrl task.id)
                      (xis.memberUrl memberNum)
                      (Just <| PointInTime.toCalendarDate kioskModel.currTime)
                      WorkingClaimStatus
                      []  -- REVIEW: Arbitrary because encoder ignores.
                  )
                  result2Msg
          in
            (sceneModel, upsertCmd)
        Nothing ->
          ({sceneModel | badNews=["You must choose a task to work!"]}, Cmd.none)

    TL_ClaimUpsertResult (Ok claim) ->
      let
        createWorkCmd =
          xis.createWork
            ( WorkData
                (xis.claimUrl claim.id)  -- claim
                Nothing  -- witness
                (PointInTime.toCalendarDate kioskModel.currTime)  -- workDate
                Nothing  -- WorkDuration
                (Just <| PointInTime.toClockTime kioskModel.currTime)  -- WorkStartTime
            )
            (TaskListVector << TL_WorkInsertResult)
      in
        (sceneModel, createWorkCmd)

    TL_WorkInsertResult (Ok claim) ->
        (sceneModel, segueTo TaskInfo)

    -- -- -- -- ERROR HANDLERS -- -- -- --

    TL_TaskListResult (Err error) ->
      ({sceneModel | workableTasks=Failed (toString error)}, Cmd.none)

    TL_ClaimUpsertResult (Err error) ->
      ({sceneModel | badNews=[toString error]}, Cmd.none)

    TL_WorkInsertResult (Err error) ->
      ({sceneModel | badNews=[toString error]}, Cmd.none)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

idxTaskListScene = mdlIdBase TaskList


view : KioskModel a -> Html Msg
view kioskModel =
  let sceneModel = kioskModel.taskListModel
  in case sceneModel.workableTasks of

    Pending -> waitingView kioskModel
    Received tasks -> chooseView kioskModel tasks
    Failed err -> errorView kioskModel err


waitingView : KioskModel a -> Html Msg
waitingView kioskModel =
  let
    sceneModel = kioskModel.taskListModel
  in
    genericScene kioskModel
      "One Moment Please!"
      "I'm fetching a list of tasks for you"
      (text "")  -- REVIEW: Probably won't be on-screen long enough to merit a spinny graphic.
      [] -- no buttons
      [] -- no errors


errorView : KioskModel a -> String -> Html Msg
errorView kioskModel err =
  let
    sceneModel = kioskModel.taskListModel
  in
    genericScene kioskModel
      "Choose a Task"
      "Please see a staff member"
      (text "")
      [ ButtonSpec "OK" (msgForSegueTo OldBusiness) ]
      [err]


chooseView : KioskModel a -> List XisApi.Task -> Html Msg
chooseView kioskModel tasks =
  let
    sceneModel = kioskModel.taskListModel
  in
    genericScene kioskModel
      "Choose a Task"
      "Here are some you can work"
      ( taskChoices kioskModel tasks)
      [ ButtonSpec "OK" (TaskListVector <| TL_ValidateTaskChoice) ]
      sceneModel.badNews


taskChoices : KioskModel a -> List XisApi.Task -> Html Msg
taskChoices kioskModel tasks =
  let
    sceneModel = kioskModel.taskListModel
  in
    div [taskListStyle]
      ([vspace 30] ++ List.indexedMap
        (\index wt ->
          div [taskDivStyle (if wt.data.priority == HighPriority then "#ccffcc" else "#dddddd")]
            [ Toggles.radio MdlVector [idxTaskListScene, index] kioskModel.mdl
              [ Toggles.value
                (case sceneModel.selectedTask of
                  Nothing -> False
                  Just st -> st == wt
                )
              , Options.onToggle (TaskListVector <| TL_ToggleTask <| wt)
              ]
              [text wt.data.shortDesc]
            ]
        )
        tasks
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
