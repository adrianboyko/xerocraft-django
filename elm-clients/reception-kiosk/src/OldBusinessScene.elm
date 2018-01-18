
module OldBusinessScene exposing (init, sceneWillAppear, update, view, OldBusinessModel)

-- Standard
import Html exposing (Html, div, text, span)
import Html.Attributes exposing (src, width, style)

-- Third Party
import Maybe.Extra as MaybeX
import Material.Toggles as Toggles
import Material.Options as Options
import List.Extra as ListX
import List.Nonempty as NonEmpty

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
  }


type alias OldBusinessModel =
  { oldBusiness : List OldBusinessItem
  , selectedItem : Maybe OldBusinessItem
  }


init : Flags -> (OldBusinessModel, Cmd Msg)
init flags =
  ( { oldBusiness = []
    , selectedItem = Nothing
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

      (OldBusiness, ReasonForVisit) -> checkForOldBusiness kioskModel

      (OldBusiness, MembersOnly) -> checkForOldBusiness kioskModel

      (OldBusiness, TaskInfo) -> checkForOldBusiness kioskModel

      (OldBusiness, CheckOut) -> checkForOldBusiness kioskModel

      (_, _) -> (sceneModel, Cmd.none)


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
    ({sceneModel | oldBusiness=[]}, cmd)


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

      -- This case starts the lookup of tasks corresponding to the open claims.
      OB_WorkingClaimsResult (Ok {results}) ->
        let
          claims = filterSelectedTask kioskModel results
          tagger c = OldBusinessVector << (OB_NoteRelatedTask c)
          getTaskCmd c = xis.getTaskFromUrl c.data.claimedTask (tagger c)
          getTaskCmds = List.map getTaskCmd claims
        in
          if List.isEmpty claims then
            (sceneModel, segueTo CheckInDone)
          else
            (sceneModel, Cmd.batch getTaskCmds)

      OB_NoteRelatedTask claim (Ok task) ->
        let
          newOldBusiness = (OldBusinessItem task claim) :: sceneModel.oldBusiness
        in
          ({sceneModel | oldBusiness=newOldBusiness}, Cmd.none)

      OB_DeleteSelectedClaim ->
        (sceneModel, Cmd.none)

      ----------------------------------

      OB_WorkingClaimsResult (Err error) ->
        -- It's not a show stopper if this fails. Just log and move on to next scene.
        let _ = Debug.log (toString error)
        in (sceneModel, segueTo CheckInDone)

      OB_NoteRelatedTask claim (Err error) ->
        -- It's not a show stopper if this fails. Just log and move on to next scene.
        let _ = Debug.log (toString error)
        in (sceneModel, segueTo CheckInDone)

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
        ("You have " ++ tPhrase ++ " in progress!")
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
        , ButtonSpec "Delete" (OldBusinessVector <| OB_DeleteSelectedClaim) isSelection
        , let
            nextScene =
              -- User can only get here via CheckIn or CheckOut.
              if NonEmpty.member CheckIn kioskModel.sceneStack
                then CheckInDone else CheckOutDone
          in
            ButtonSpec "Skip" (msgForSegueTo nextScene) True
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
    nStr ++ if n>1 then " tasks" else " task"


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------


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
