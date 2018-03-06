
module TaskInfoScene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , TaskInfoModel
  )

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
import XisRestApi as XisApi exposing (Member)

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
  , taskInfoModel : TaskInfoModel
  }


type alias TaskInfoModel =
  ---------- REQ'D ARGS:
  { member : Maybe Member
  , task : Maybe XisApi.Task
  , claim : Maybe XisApi.Claim
  ---------- NO OTHER STATE
  }


args x =
  ( x.member
  , x.task
  , x.claim
  )


init : Flags -> (TaskInfoModel, Cmd Msg)
init flags =
  ( { member = Nothing
    , task = Nothing
    , claim = Nothing
    }
  , Cmd.none)


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

update : TaskInfoMsg -> KioskModel a -> (TaskInfoModel, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.taskInfoModel
  in case msg of
    TI_Segue (member, task, claim) ->
      ( { sceneModel
        | member = Just member
        , task = Just task
        , claim = Just claim
        }
      , send <| WizardVector <| Push TaskInfo
      )


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  case args kioskModel.taskInfoModel of

    (Just member, Just task, Just claim) ->
      genericScene kioskModel
        "Thanks for Helping!"
        "Instructions Follow:"
        (div [instructionDiv]
          [ vspace 20
          , p [instructionPara] [text task.data.instructions]
          , vspace 30
          , text "When the task is completed, return to this kiosk and use Check Out to close it."
          , vspace 20
          ]
        )
        [ButtonSpec "Got It!" (OldBusinessVector <| OB_SegueB (CheckInSession, member, claim)) True]
        []  -- Never any bad news for this scene.

    _ ->
      errorView kioskModel missingArguments


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
