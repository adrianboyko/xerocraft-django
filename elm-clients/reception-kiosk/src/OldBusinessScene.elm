
module OldBusinessScene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , OldBusinessModel
  , OldBusinessItem
  )

-- Standard
import Html exposing (Html, div, text, span)
import Html.Attributes exposing (src, width, style)

-- Third Party
import Maybe.Extra as MaybeX
import Material.Toggles as Toggles
import Material.Options as Options
import List.Extra as ListX
import List.Nonempty as NonEmpty
import Update.Extra as UpdateX exposing (addCmd)

-- Local
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import XisRestApi as XisApi exposing (..)
import DjangoRestFramework exposing (idFromUrl)
import Fetchable exposing (..)
import CheckInScene exposing (CheckInModel)
import CheckOutScene exposing (CheckOutModel)
import TaskListScene exposing (TaskListModel)
import CalendarDate as CD


-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------

idxOldBusinessScene = mdlIdBase OldBusiness


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  ( SceneUtilModel
    { a
    | oldBusinessModel : OldBusinessModel
    , checkInModel : CheckInModel
    , checkOutModel : CheckOutModel
    , taskListModel : TaskListModel
    , xisSession : XisApi.Session Msg
    }
  )


type alias OldBusinessItem =
  { task: XisApi.Task
  , claim: XisApi.Claim
  , work: XisApi.Work  -- If they're not working it, it's not old/unfinished business.
  }


type alias OldBusinessModel =
  { oldBusiness : List OldBusinessItem
  , selectedItem : Maybe OldBusinessItem
  , workResponsesExpected : Maybe Int
  , workResponsesReceived : Int
  }


init : Flags -> (OldBusinessModel, Cmd Msg)
init flags =
  ( { oldBusiness = []
    , selectedItem = Nothing
    , workResponsesExpected = Nothing
    , workResponsesReceived = 0
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
    case (appearing, vanishing) of

      -- Arriving at scene after looping back from a COMPLETED Timesheet sequence.
      -- Trim out the loop since we don't want user to be able to go forward through it again.
      (OldBusiness, TimeSheetPt3) ->
        let
          onStack x = NonEmpty.member x kioskModel.sceneStack
          popCmd = rebaseTo OldBusiness
        in
          checkForOldBusiness kioskModel |> addCmd popCmd

      -- Arriving at scene in forward direction or reverse direction WITHOUT a completed Timesheet.
      (OldBusiness, _) ->
        checkForOldBusiness kioskModel

      -- Ignore all others.
      (_, _) ->
        (sceneModel, Cmd.none)


memberId : KioskModel a -> Int
memberId kioskModel =
  if NonEmpty.member CheckIn kioskModel.sceneStack then
    case kioskModel.checkInModel.checkedInMember of
      Just memb -> memb.id
      Nothing ->
        -- We shouldn't get to this scene without there being a checkedInMember.
        -- If it happens, lets log a msg and return a bogus member num.
        -- Providing a bogus member num will cause this scene to be a no-op.
        let _ = Debug.log "checkInMember" Nothing
        in -99
  else
    kioskModel.checkOutModel.checkedOutMemberNum


checkForOldBusiness : KioskModel a -> (OldBusinessModel, Cmd Msg)
checkForOldBusiness kioskModel =
  let
    sceneModel = kioskModel.oldBusinessModel
    tagging = (OldBusinessVector << OB_WorkingClaimsResult)
    cmd = kioskModel.xisSession.listClaims
      [ ClaimingMemberEquals <| memberId kioskModel
      , ClaimStatusEquals WorkingClaimStatus
      ]
      tagging
  in
    ( { sceneModel
      | oldBusiness=[]
      , selectedItem=Nothing
      , workResponsesExpected=Nothing -- We'll know when we get the claims.
      , workResponsesReceived=0
      }
    , cmd
    )


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : OldBusinessMsg -> KioskModel a -> (OldBusinessModel, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.oldBusinessModel
    xis = kioskModel.xisSession
    theNextScene = nextScene kioskModel
  in
    case msg of

      -- This case starts the lookup of tasks corresponding to the open claims.
      OB_WorkingClaimsResult (Ok {results}) ->
        let
          claims = filterSelectedTask kioskModel results
          tagger c = OldBusinessVector << (OB_NoteRelatedTask c)
          getTaskCmd c = xis.getTaskFromUrl c.data.claimedTask (tagger c)
          getTaskCmds = List.map getTaskCmd claims
          expected = List.sum <| List.map (List.length << .workSet << .data) claims
        in
          if List.isEmpty claims then
            (sceneModel, segueTo theNextScene)
          else
            ({sceneModel | workResponsesExpected=Just expected}, Cmd.batch getTaskCmds)

      -- This case starts the lookup of works corresponding to the open claims.
      OB_NoteRelatedTask claim (Ok task) ->
        let
          tagger = OldBusinessVector << OB_NoteRelatedWork task claim
          getWorkCmd resUrl = xis.getWorkFromUrl resUrl tagger
          getWorkCmds = List.map getWorkCmd claim.data.workSet
        in
          if List.isEmpty getWorkCmds then
            (sceneModel, Cmd.none)
          else
            (sceneModel, Cmd.batch getWorkCmds)

      -- We're only interested in claims that have an associated work record.
      -- And that work record should have blank duration.
      OB_NoteRelatedWork task claim (Ok work) ->
        let
          newOldBusiness = (OldBusinessItem task claim work) :: sceneModel.oldBusiness
          newCount = sceneModel.workResponsesReceived + 1
          newSceneModel = case work.data.workDuration of
            Nothing -> {sceneModel | oldBusiness=newOldBusiness, workResponsesReceived=newCount}
            Just _ -> {sceneModel | workResponsesReceived=newCount}
        in
          considerSkip newSceneModel theNextScene

      OB_DeleteSelection ->
        case sceneModel.selectedItem of

          Just {task, claim, work} ->
            let
              cmd = xis.deleteWorkById work.id (OldBusinessVector << OB_NoteWorkDeleted)
              newModel = {sceneModel | selectedItem=Nothing }
            in
              (newModel, cmd)

          Nothing ->
            -- Shouldn't get here since there must be a selction in order to click "DELETE"
            (sceneModel, Cmd.none)

      OB_NoteWorkDeleted _ ->
        checkForOldBusiness kioskModel

      OB_ToggleItem claimId ->
        let
          finder item = item.claim.id == claimId
          item = ListX.find finder sceneModel.oldBusiness
        in
          case item of
            Nothing ->
              (sceneModel, Cmd.none)
            Just i ->
              ({sceneModel | selectedItem = Just i}, Cmd.none)

      ----------------------------------

      OB_WorkingClaimsResult (Err error) ->
        -- It's not a show stopper if this fails. Just log and move on to next scene.
        let _ = Debug.log (toString error)
        in (sceneModel, segueTo theNextScene)

      OB_NoteRelatedTask claim (Err error) ->
        let
          count = List.length <| claim.data.workSet
          newReceived = sceneModel.workResponsesReceived + count
          newSceneModel = {sceneModel | workResponsesReceived=newReceived}
        in
          considerSkip newSceneModel theNextScene

      OB_NoteRelatedWork task claim (Err error) ->
        let
          newReceived = sceneModel.workResponsesReceived + 1
          newSceneModel = {sceneModel | workResponsesReceived=newReceived}
        in
          considerSkip newSceneModel theNextScene


considerSkip : OldBusinessModel -> Scene -> (OldBusinessModel, Cmd Msg)
considerSkip sceneModel theNextScene =
  case sceneModel.workResponsesExpected of

    Nothing ->
      (sceneModel, Cmd.none)

    Just expected ->
      if sceneModel.workResponsesReceived == expected then
        -- We have received all the expected responses, so decide whether or not to skip.
        if List.length sceneModel.oldBusiness > 0 then
          (sceneModel, Cmd.none)
        else
          (sceneModel, segueTo theNextScene)
      else
        -- We have not yet received all the expected responses, so don't do anything...
        (sceneModel, Cmd.none)


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
    isSelection = MaybeX.isJust sceneModel.selectedItem
  in
    if List.isEmpty sceneModel.oldBusiness then
      blankGenericScene kioskModel
    else
      let tPhrase = taskPhrase sceneModel.oldBusiness
      in
        genericScene kioskModel
        ("You Have " ++ tPhrase ++ " In Progress!")
        "Let's Review Them"
        (div [sceneTextStyle] 
          [ vspace 25
          , text ("Select any that is already completed")
          , vspace 0
          , text "and then click 'FINISH' to fill in a timesheet"
          , vspace 0
          , text "or 'DELETE' if it was not actually worked."
          , vspace 20
          , oldBusinessChoices kioskModel sceneModel.oldBusiness
          ]
        )
        [ ButtonSpec "Finish" (msgForSegueTo TimeSheetPt1) isSelection
        , ButtonSpec "Delete" (OldBusinessVector <| OB_DeleteSelection) isSelection
        , ButtonSpec "Skip" (msgForSegueTo (nextScene kioskModel)) True
        ]
        []  -- Never any bad news for this scene.


oldBusinessChoices : KioskModel a -> List OldBusinessItem -> Html Msg
oldBusinessChoices kioskModel business =
  let
    sceneModel = kioskModel.oldBusinessModel
  in
    div [businessListStyle]
      (List.indexedMap
        (\index item ->
          div [businessDivStyle "#dddddd"]
            [ Toggles.radio MdlVector [idxOldBusinessScene, index] kioskModel.mdl
              [ Toggles.value
                (case sceneModel.selectedItem of
                  Nothing -> False
                  Just i -> i == item
                )
              , Options.onToggle (OldBusinessVector <| OB_ToggleItem <| item.claim.id)
              ]
              [viewOldBusinessItem item]
            ]
        )
        business
      )

viewOldBusinessItem : OldBusinessItem -> Html Msg
viewOldBusinessItem {task, claim} =
  let
    tDesc = task.data.shortDesc
    tDate = CD.format "%a %b %ddd" task.data.scheduledDate |> CD.superOrdinals
  in
    span [] [text <| tDesc ++ ", ", tDate]


taskPhrase : List a -> String
taskPhrase l =
  let
    n = List.length l
    nStr = toString n
  in
    nStr ++ if n>1 then " Tasks" else " Task"


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------

-----------------------------------------------------------------------------
-- UTILITIEs
-----------------------------------------------------------------------------

nextScene : KioskModel a -> Scene
nextScene kioskModel =
  -- User can only get here via CheckIn or CheckOut.
  if NonEmpty.member CheckIn kioskModel.sceneStack
    then CheckInDone else CheckOutDone

-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

businessListStyle = style
  [ "width" => "500px"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "text-align" => "left"
  ]

businessDivStyle color = style
  [ "background-color" => color
  , "padding" => "10px"
  , "margin" => "15px"
  , "border-radius" => "20px"
  ]
