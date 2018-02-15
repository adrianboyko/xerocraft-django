
module TaskInfoScene exposing (init, sceneWillAppear, view, TaskInfoModel)

-- Standard
import Html exposing (Html, text, div, p)
import Html.Attributes exposing (style)

-- Third Party
import Material
import List.Nonempty exposing (Nonempty)

-- Local
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import TaskListScene exposing (TaskListModel)


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias TaskInfoModel =
  {
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  { a
  ------------------------------------
  | mdl : Material.Model
  , flags : Flags
  , sceneStack : Nonempty Scene
  ------------------------------------
  , taskInfoModel : TaskInfoModel
  , taskListModel : TaskListModel
  }

init : Flags -> (TaskInfoModel, Cmd Msg)
init flags = ({}, Cmd.none)


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> Scene -> (TaskInfoModel, Cmd Msg)
sceneWillAppear kioskModel appearing vanishing =
  let
    sceneModel = kioskModel.taskInfoModel
  in
    case (appearing, vanishing) of

      (TaskInfo, _) ->
        -- If user gets to Task Info, we rebase the scene stack to prevent going back.
        (sceneModel, rebase)

      _ ->
        (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.taskInfoModel
    taskListModel = kioskModel.taskListModel
    instructions =
      case taskListModel.selectedTask of
        Just opsTask -> opsTask.data.instructions
        Nothing -> "Please see a Staff Member for instructions."
  in
    genericScene kioskModel
      "Thanks for Helping!"
      "Instructions Follow:"
      (div [instructionDiv]
        [ vspace 20
        , p [instructionPara] [text instructions]
        , vspace 30
        , text "When the task is completed, return to this kiosk and use Check Out to close it."
        , vspace 20
        ]
      )
      [ButtonSpec "Got It!" (msgForSegueTo OldBusiness) True]
      []  -- Never any bad news for this scene.


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

instructionDiv = style
  [ "width" => "650px"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "line-height" => "1"
  ]

instructionPara = style
  [ "font-size" => "16pt"
  ]
