
module OldBusinessScene exposing (init, sceneWillAppear, update, view, OldBusinessModel)

-- Standard
import Html exposing (Html, div, text, img, br)
import Html.Attributes exposing (src, width, style)

-- Third Party
import Maybe.Extra as MaybeX

-- Local
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import XisRestApi as XisApi exposing (..)
import DjangoRestFramework exposing (idFromUrl)
import Fetchable exposing (..)
import CheckInScene exposing (CheckInModel)
import TaskListScene exposing (TaskListModel)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  ( SceneUtilModel
    { a
    | oldBusinessModel : OldBusinessModel
    , checkInModel : CheckInModel
    , taskListModel : TaskListModel
    , xisSession : XisApi.Session Msg
    }
  )


type alias OldBusinessModel =
  { oldOpenClaims : Fetchable (List XisApi.Claim)
  }


init : Flags -> (OldBusinessModel, Cmd Msg)
init flags =
  ( { oldOpenClaims = Pending
    }
  , Cmd.none
  )


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> Scene -> (OldBusinessModel, Cmd Msg)
sceneWillAppear kioskModel appearing vanishing =
  let
    sceneModel = kioskModel.oldBusinessModel
  in
    -- This OldBusiness scene will only appear on flows from CheckIn.
    case (appearing, vanishing) of

      (OldBusiness, ReasonForVisit) -> checkForOldBusiness kioskModel

      (OldBusiness, MembersOnly) -> checkForOldBusiness kioskModel

      (OldBusiness, TaskInfo) -> checkForOldBusiness kioskModel

      (_, _) -> (sceneModel, Cmd.none)


checkForOldBusiness : KioskModel a -> (OldBusinessModel, Cmd Msg)
checkForOldBusiness kioskModel =
  let
    sceneModel = kioskModel.oldBusinessModel
    checkInModel = kioskModel.checkInModel
    xis = kioskModel.xisSession
    cmd = xis.listClaims
      [ ClaimingMemberEquals checkInModel.memberNum
      , ClaimStatusEquals WorkingClaimStatus
      ]
      (OldBusinessVector << OB_WorkingClaimsResult)
  in
    (sceneModel, cmd)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : OldBusinessMsg -> KioskModel a -> (OldBusinessModel, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.oldBusinessModel
    xis = kioskModel.xisSession

  in
    case msg of

      OB_WorkingClaimsResult (Ok {results}) ->
        let
          filteredResults = filterSelectedTask kioskModel results
        in
          if List.isEmpty filteredResults then
            (sceneModel, segueTo CheckInDone)
          else
            ({sceneModel | oldOpenClaims = Received filteredResults}, Cmd.none)

      OB_WorkingClaimsResult (Err error) ->
        -- It's not a show stopper if this fails. Just log and move on to next scene.
        let
          _ = Debug.log (toString error)
        in
          (sceneModel, segueTo CheckInDone)


-- The user might have just selected a task to work.
-- If so, we don't want it to appear as "Old Business", so filter it out.
filterSelectedTask : KioskModel a -> List XisApi.Claim -> List XisApi.Claim
filterSelectedTask kioskModel claims =
  case kioskModel.taskListModel.selectedTask of
    Just task ->
      List.filter (\claim -> (idFromUrl claim.data.claimedTask) /= Ok task.id) claims
    Nothing ->
      claims


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.oldBusinessModel
  in
    case sceneModel.oldOpenClaims of

      Received results ->
        let (taskPhrase, sheetPhrase) = phrases results
        in
          genericScene kioskModel
          "Unfinished Business"
          ""
          (div [sceneTextStyle]
            [ vspace 50
            , text ("You previously started " ++ taskPhrase ++ " but")
            , vspace 0
            , text ("didn't complete " ++ sheetPhrase)
            , vspace 0
            , text "Let's do that now so you receive credit!"
            , vspace 20
            ]
          )
          [ ButtonSpec "OK!" (msgForSegueTo TimeSheetPt1)
          , ButtonSpec "Skip" (msgForSegueTo CheckInDone)
          ]
          []  -- Never any bad news for this scene.

      _ ->
        blankGenericScene kioskModel

phrases : List XisApi.Claim -> (String, String)
phrases claims =
  let
    n = List.length claims
    nStr = toString n
  in
    if n > 1 then
      (nStr ++ " tasks", "timesheets for them.")
    else
      (nStr ++ " task", "a timesheet for it.")


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

bottomImgStyle = style
  [ "text-align" => "center"
  , "padding-left" => "30px"
  , "padding-right" => "0"
  ]