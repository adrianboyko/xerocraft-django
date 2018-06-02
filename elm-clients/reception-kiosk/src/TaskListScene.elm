
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
import Material
import Material.Toggles as Toggles
import Material.Options as Options exposing (css)
import Material.List as Lists
import Maybe.Extra as MaybeX exposing (isNothing)
import List.Extra as ListX
import List.Nonempty exposing (Nonempty)

-- Local
import XisRestApi as XisApi exposing (..)
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import Fetchable exposing (..)
import DjangoRestFramework as DRF
import PointInTime exposing (PointInTime)


-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------

staffingStatus_STAFFED = "S"  -- As defined in Django backend.
taskPriority_HIGH = "H"  -- As defined in Django backend.
idxTaskListScene = mdlIdBase TaskList


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  { a
  ------------------------------------
  | mdl : Material.Model
  , flags : Flags
  , sceneStack : Nonempty Scene
  ------------------------------------
  , currTime : Time
  , taskListModel : TaskListModel
  , xisSession : XisApi.Session Msg
  }


type alias TaskListModel =
  ------------- Req'd Args:
  { member : Maybe Member
  ------------- Other State:
  , todaysTasks : Fetchable (List XisApi.Task)
  , workableTasks : List XisApi.Task
  , selectedTask : Maybe XisApi.Task
  , claimOnSelectedTask : Maybe Claim
  , badNews : List String
  }


args x =
  ( x.member
  )


init : Flags -> (TaskListModel, Cmd Msg)
init flags =
  let sceneModel =
    ------------- Req'd Args:
    { member = Nothing
    ------------- Other State:
    , todaysTasks = Pending
    , workableTasks = []
    , selectedTask = Nothing
    , claimOnSelectedTask = Nothing
    , badNews = []
    }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> Scene -> (TaskListModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene vanishingScene =
  let sceneModel = kioskModel.taskListModel
  in case (appearingScene, vanishingScene) of

    (ReasonForVisit, _) ->
      -- Start fetching workable tasks b/c they *might* be on their way to this (TaskList) scene.
      getTodaysTasks kioskModel

    (TaskList, TaskInfo) ->
      -- User hit back button. Since workable task data was changed by prev visit to this scene, we need to reget it.
      getTodaysTasks kioskModel

    (TaskList, _) ->
      case args sceneModel of
        (Just _) ->
          (sceneModel, Cmd.none)
        _ ->
          (sceneModel, send <| ErrorVector <| ERR_Segue missingArguments)

    _ ->
      (sceneModel, Cmd.none)


getTodaysTasks : KioskModel a -> (TaskListModel, Cmd Msg)
getTodaysTasks kioskModel =
  let
    sceneModel = kioskModel.taskListModel
    currDate = PointInTime.toCalendarDate kioskModel.currTime
    cmd = kioskModel.xisSession.listTasks
      [ScheduledDateEquals currDate]
      (TaskListVector << TL_TaskListResult)
  in
    ({sceneModel | todaysTasks=Pending}, cmd)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

determineWorkableTasks : TaskListModel -> XisApi.Session Msg -> TaskListModel
determineWorkableTasks sceneModel xis =
  case (sceneModel.todaysTasks, sceneModel.member) of

    (Received todaysTasks, Just member) ->
      let
        -- The more normal case is to offer up tasks that the user can claim:
        memberCanClaimTest = xis.memberCanClaimTask member.id
        claimableTasks = List.filter memberCanClaimTest todaysTasks

        -- We also want to know which task(s) (if any) have already been claimed:
        isCurrentClaimant = xis.memberHasStatusOnTask member.id CurrentClaimStatus
        claimedTask = ListX.find isCurrentClaimant claimableTasks
      in
        { sceneModel
        | workableTasks = claimableTasks
        , selectedTask = claimedTask
        }

    _ -> sceneModel


update : TaskListMsg -> KioskModel a -> (TaskListModel, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.taskListModel
    flags = kioskModel.flags
    xis = kioskModel.xisSession

  in case msg of

    TL_Segue member ->
      let
        newSceneModel =
          determineWorkableTasks
            { sceneModel | member = Just member }
            xis
      in
        (newSceneModel, send <| WizardVector <| Push TaskList)

    -- This will accumulate tasks but we don't yet know who the member is,
    -- so processing of accumulated tasks will be defered to view.
    TL_TaskListResult (Ok {results, next}) ->
      -- TODO: Deal with the possibility of paged results (i.e. next is not Nothing)?
      let
        newSceneModel =
          determineWorkableTasks
            { sceneModel | todaysTasks = Received results }
            xis
      in
        (newSceneModel, Cmd.none)

    TL_ToggleTask toggledTask ->
      ( { sceneModel
        | selectedTask = Just toggledTask
        , badNews = []
        }
      , Cmd.none
      )

    TL_ValidateTaskChoice ->
      case sceneModel.member of
        Nothing ->
          (sceneModel, send <| ErrorVector <| ERR_Segue missingArguments)
        Just m ->
          case sceneModel.selectedTask of
            Just task ->
              let
                result2Msg = TaskListVector << TL_ClaimUpsertResult
                existingClaim = xis.membersClaimOnTask m.id task
                upsertCmd = case existingClaim of

                  Just c ->
                    let
                      claimMod = c |> setClaimsStatus WorkingClaimStatus
                    in
                      xis.replaceClaim claimMod result2Msg

                  Nothing ->
                    xis.createClaim
                      { claimedDuration = Maybe.withDefault 0.0 task.data.workDuration
                      , claimedStartTime = Just <| PointInTime.toClockTime kioskModel.currTime
                      , dateVerified = Just <| PointInTime.toCalendarDate kioskModel.currTime
                      , claimedTask = xis.taskUrl task.id
                      , claimingMember = xis.memberUrl m.id
                      , status = WorkingClaimStatus
                      , workSet = []  -- REVIEW: This is an incoming field only. Not used in create.
                      }
                      result2Msg
              in
                (sceneModel, upsertCmd)
            Nothing ->
              ({sceneModel | badNews=["You must choose a task to work!"]}, Cmd.none)

    TL_ClaimUpsertResult (Ok claim) ->
      let
        currClockTime = PointInTime.toClockTime kioskModel.currTime
        createWorkCmd =
          xis.createWork
            { claim = xis.claimUrl claim.id
            , witness = Nothing
            , workDate = PointInTime.toCalendarDate kioskModel.currTime
            , workDuration = Nothing
            , workStartTime = Just currClockTime
            }
            (TaskListVector << TL_WorkInsertResult)
      in
        ({sceneModel | claimOnSelectedTask=Just claim}, createWorkCmd)

    TL_WorkInsertResult (Ok w) ->
      case (sceneModel.member, sceneModel.selectedTask, sceneModel.claimOnSelectedTask) of
        (Just m, Just t, Just c) ->
          (sceneModel, send <| TaskInfoVector <| TI_Segue m (TaskClaimWork t c w))
        (_, _, _) ->
          (sceneModel, send <| ErrorVector <| ERR_Segue "Missing member or selected task.")


    -- -- -- -- ERROR HANDLERS -- -- -- --

    TL_TaskListResult (Err error) ->
      ({sceneModel | todaysTasks=Failed (toString error)}, Cmd.none)

    TL_ClaimUpsertResult (Err error) ->
      ({sceneModel | badNews=[toString error]}, Cmd.none)

    TL_WorkInsertResult (Err error) ->
      ({sceneModel | badNews=[toString error]}, Cmd.none)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.taskListModel
  in
    case sceneModel.member of
      Just m ->
        case sceneModel.todaysTasks of
          Pending -> waitingView kioskModel
          Received _ -> chooseView kioskModel sceneModel.workableTasks m
          Failed err -> errorView kioskModel err
      Nothing ->
        errorView kioskModel missingArguments


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


chooseView : KioskModel a -> List XisApi.Task -> Member -> Html Msg
chooseView kioskModel todaysTasks member =
  let
    sceneModel = kioskModel.taskListModel
  in
    genericScene kioskModel
      "Choose a Task"
      "Here are some you can work"
      ( taskChoices kioskModel todaysTasks)
      [ ButtonSpec "OK" (TaskListVector <| TL_ValidateTaskChoice) True]
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
