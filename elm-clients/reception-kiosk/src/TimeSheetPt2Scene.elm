
module TimeSheetPt2Scene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , TimeSheetPt2Model
  )

-- Standard
import Html exposing (Html, text, div, span)
import Html.Attributes exposing (style)

-- Third Party
import Material
import List.Nonempty exposing (Nonempty)

-- Local
import TimeSheetCommon exposing (infoDiv)
import XisRestApi as XisApi exposing (..)
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import Fetchable exposing (..)
import PointInTime exposing (PointInTime)
import CalendarDate exposing (CalendarDate)
import ClockTime exposing (ClockTime)
import Duration as Dur


-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------

idxTimeSheetPt2 = mdlIdBase TimeSheetPt2
idxOtherWorkDesc = [idxTimeSheetPt2, 1]

moreInfoReqd = "Please provide more information about the work you did."


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
  , currTime : PointInTime
  , timeSheetPt2Model : TimeSheetPt2Model
  , xisSession : XisApi.Session Msg
  }


type alias TimeSheetPt2Model =
  ---------------- Req'd Args:
  { sessionType : Maybe SessionType
  , member : Maybe Member
  , tcw : Maybe TaskClaimWork
  ---------------- Other State:
  , otherWorkDesc : String
  , badNews : List String
  }


init : Flags -> (TimeSheetPt2Model, Cmd Msg)
init flags =
  let sceneModel =
    ---------------- Req'd Args:
    { sessionType = Nothing
    , member = Nothing
    , tcw = Nothing
    ---------------- Other State:
    , otherWorkDesc = ""
    , badNews = []
    }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> Scene -> (TimeSheetPt2Model, Cmd Msg)
sceneWillAppear kioskModel appearingScene vanishingScene =
  let
    sceneModel = kioskModel.timeSheetPt2Model
  in
    case (appearingScene, vanishingScene) of

      (TimeSheetPt2, _) ->
        case (sceneModel.tcw, sceneModel.sessionType, sceneModel.member) of

          (Just tcw, Just sessionType, Just member) ->
            if tcw.task.data.shortDesc == "Other Work" then
              (sceneModel, Cmd.none)  -- focusOnIndex idxOtherWorkDesc)
            else
              -- This scene should be invisible because task is not "Other Work".
              -- User might be going forward OR BACKWARD in the wizard.
              -- Either way, don't leave this scene on the stack.
              -- Note: TS3 will REPLACE this scene on the stack, if need be.
              if vanishingScene==TimeSheetPt1 then
                (sceneModel, send <| TimeSheetPt3Vector <| TS3_Segue sessionType member tcw Nothing)
              else
                (sceneModel, pop)
          _ ->
            (sceneModel, send <| ErrorVector <| ERR_Segue missingArguments)

      (_, _) ->
        (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : TimeSheetPt2Msg -> KioskModel a -> (TimeSheetPt2Model, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.timeSheetPt2Model
    xis = kioskModel.xisSession

  in case msg of

    TS2_Segue sessionType member tcw ->
      ( { sceneModel
        | member = Just member
        , sessionType = Just sessionType
        , tcw = Just tcw
        }
      , send <| WizardVector <| Push <| TimeSheetPt2
      )

    TS2_UpdateDescription s ->
      ({sceneModel | otherWorkDesc = s}, Cmd.none)

    TS2_Continue ->
      if (sceneModel.otherWorkDesc |> String.trim |> String.length) < 10 then
        ({sceneModel | badNews=[moreInfoReqd]}, Cmd.none)
      else
        case (sceneModel.tcw, sceneModel.sessionType, sceneModel.member) of

          (Just tcw, Just sessionType, Just member) ->
            ( sceneModel
            , send <| TimeSheetPt3Vector <| TS3_Segue sessionType member tcw (Just sceneModel.otherWorkDesc)
            )

          _ ->
            (sceneModel, send <| ErrorVector <| ERR_Segue missingArguments)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  case kioskModel.timeSheetPt2Model.tcw of
    Just {task, claim, work} -> viewNormal kioskModel task claim work
    _ -> errorView kioskModel missingArguments


viewNormal : KioskModel a -> XisApi.Task -> XisApi.Claim -> XisApi.Work -> Html Msg
viewNormal kioskModel task claim work =
  let
    sceneModel = kioskModel.timeSheetPt2Model

  in genericScene kioskModel
    "Volunteer Timesheet"
    "Please describe the work you did"

    ( div []
      [ vspace 50
      , infoDiv kioskModel.currTime (SomeTCW <| TaskClaimWork task claim work) Nothing
      , vspace 70
      , div [textAreaContainerStyle]
          [ sceneTextArea kioskModel idxOtherWorkDesc
              "Description of work done" sceneModel.otherWorkDesc
              6 -- rows in text area
              (TimeSheetPt2Vector << TS2_UpdateDescription)
          ]

      , vspace 20
      ]
    )

    [ ButtonSpec "Continue" (TimeSheetPt2Vector <| TS2_Continue) True]

    sceneModel.badNews



-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

textAreaContainerStyle = style
  [ "display" => "inline-block"
  , "padding-top" => px 20
  , "border-style" => "solid"
  , "border-width" => px 1
  , "border-radius" => px 10
  , "width" => px 550
  , "background-color" => "white"
  ]