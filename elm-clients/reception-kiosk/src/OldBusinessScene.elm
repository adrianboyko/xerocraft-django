
module OldBusinessScene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , OldBusinessModel
  )

-- Standard
import Html exposing (Html, div, text, span)
import Html.Attributes exposing (src, width, style)

-- Third Party
import Maybe.Extra as MaybeX
import Material
import Material.Toggles as Toggles
import Material.Options as Options
import List.Extra as ListX
import List.Nonempty as NonEmpty exposing (Nonempty)
import Update.Extra as UpdateX exposing (addCmd)

-- Local
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import XisRestApi as XisApi exposing (..)
import DjangoRestFramework exposing (idFromUrl)
import Fetchable exposing (..)
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
  { a
  ------------------------------------
  | mdl : Material.Model
  , flags : Flags
  , sceneStack : Nonempty Scene
  ------------------------------------
  , oldBusinessModel : OldBusinessModel
  , xisSession : XisApi.Session Msg
  }


type alias OldBusinessModel =
  ---------------- Req'd Args:
  { sessionType : Maybe SessionType
  , member : Maybe Member
  ---------------- Optional Args:
  , thisSessionsClaim : Maybe Claim
  ---------------- Other State:
  , allOldBusiness : List TaskClaimWork
  , selectedItem : Maybe TaskClaimWork
  , workResponsesExpected : Maybe Int
  , workResponsesReceived : Int
  }


requiredArgs x =
  ( x.sessionType
  , x.member
  )


init : Flags -> (OldBusinessModel, Cmd Msg)
init flags =
  ( ---------------- Req'd Args:
    { sessionType = Nothing
    , member = Nothing
    ---------------- Optional Args:
    , thisSessionsClaim = Nothing
    ---------------- Other State:
    , allOldBusiness = []
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
  let
    sceneModel = kioskModel.oldBusinessModel
  in
    case sceneModel.member of
      Just memb -> memb.id
      Nothing ->
        -- We shouldn't get to this scene without there being a member.
        -- If it happens, lets log a msg and return a bogus member num.
        -- Providing a bogus member num will cause this scene to be a no-op.
        let _ = Debug.log "checkInMember" Nothing
        in -99


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
      | allOldBusiness=[]
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
  in
    case msg of

      OB_SegueA (sessionType, member) ->
        ( {sceneModel | sessionType = Just sessionType, member = Just member}
        , send <| WizardVector <| Push <| OldBusiness
        )

      OB_SegueB (sessionType, member, thisSessionsClaim) ->
        ( { sceneModel
          | sessionType = Just sessionType
          , member = Just member
          , thisSessionsClaim = Just thisSessionsClaim
          }
        , send <| WizardVector <| Push <| OldBusiness
        )

      -- This case starts the lookup of tasks corresponding to the open claims.
      OB_WorkingClaimsResult (Ok {results}) ->
        let
          -- We don't want the claim associated with the task the user just started, if any.
          claims = case sceneModel.thisSessionsClaim of
            Just c -> List.filter (\x -> x.id /= c.id) results
            Nothing -> results
          tagger c = OldBusinessVector << (OB_NoteRelatedTask c)
          getTaskCmd c = xis.getTaskFromUrl c.data.claimedTask (tagger c)
          getTaskCmds = List.map getTaskCmd claims
          expected = List.sum <| List.map (List.length << .workSet << .data) claims
        in
          if expected == 0 then
            (sceneModel, segueToDone sceneModel)
          else
            ({sceneModel | workResponsesExpected=Just expected}, Cmd.batch getTaskCmds)

      -- This case starts the lookup of works corresponding to the open claims.
      OB_NoteRelatedTask claim (Ok task) ->
        let
          tagger = OldBusinessVector << OB_NoteRelatedWork task claim
          getWorkCmd resUrl = xis.getWorkFromUrl resUrl tagger
          getWorkCmds = List.map getWorkCmd claim.data.workSet
        in
          (sceneModel, Cmd.batch getWorkCmds)

      -- We're only interested in claims that have an associated work record.
      -- And that work record should have blank duration.
      OB_NoteRelatedWork task claim (Ok work) ->
        let
          allOldBusinessPlus = TaskClaimWork task claim work :: sceneModel.allOldBusiness
          newCount = sceneModel.workResponsesReceived + 1
          newSceneModel = case work.data.workDuration of
            Nothing -> {sceneModel | allOldBusiness=allOldBusinessPlus, workResponsesReceived=newCount}
            Just _ -> {sceneModel | workResponsesReceived=newCount}
        in
          considerSkip newSceneModel

      OB_DeleteSelection ->
        case sceneModel.selectedItem of

          Just {task, claim, work} ->
            let
              cmd1 = xis.deleteWorkById work.id (OldBusinessVector << OB_NoteWorkDeleted)
              cmd2 =
                if List.length claim.data.workSet == 1 then
                  -- We're deleting the last work so the user is no longer working the claim.
                  -- So, change the status from Working to Abandoned.
                  xis.replaceClaim
                    (setClaimsStatus AbandonedClaimStatus claim)
                    (OldBusinessVector << OB_NoteClaimUpdated)
                else
                  Cmd.none
              newModel = {sceneModel | selectedItem=Nothing }
            in
              (newModel, Cmd.batch [cmd1, cmd2])

          Nothing ->
            -- Shouldn't get here since there must be a selction in order to click "DELETE"
            (sceneModel, Cmd.none)

      OB_NoteClaimUpdated (Ok _) ->
        -- No action required.
        (sceneModel, Cmd.none)

      OB_NoteWorkDeleted _ ->
        checkForOldBusiness kioskModel

      OB_ToggleItem claimId ->
        let
          finder item = item.claim.id == claimId
          item = ListX.find finder sceneModel.allOldBusiness
        in
          case item of
            Nothing ->
              (sceneModel, Cmd.none)
            Just i ->
              ({sceneModel | selectedItem = Just i}, Cmd.none)

      ----------------------------------

      OB_WorkingClaimsResult (Err error) ->
        -- It's not a show stopper if this fails. Just log and move on to next scene.
        let _ = Debug.log "WARNING" (toString error)
        in (sceneModel, segueToDone sceneModel)

      OB_NoteRelatedTask claim (Err error) ->
        let
          count = List.length <| claim.data.workSet
          newReceived = sceneModel.workResponsesReceived + count
          newSceneModel = {sceneModel | workResponsesReceived=newReceived}
        in
          considerSkip newSceneModel

      OB_NoteRelatedWork task claim (Err error) ->
        let
          newReceived = sceneModel.workResponsesReceived + 1
          newSceneModel = {sceneModel | workResponsesReceived=newReceived}
        in
          considerSkip newSceneModel

      OB_NoteClaimUpdated (Err error) ->
        -- This is a non-critical error, so let's log it and do nothing.
        let _ = Debug.log "WARNING" (toString error)
        in (sceneModel, Cmd.none)


considerSkip : OldBusinessModel -> (OldBusinessModel, Cmd Msg)
considerSkip sceneModel =
  case sceneModel.workResponsesExpected of

    Nothing ->
      (sceneModel, Cmd.none)

    Just expected ->
      if sceneModel.workResponsesReceived == expected then
        -- We have received all the expected responses, so decide whether or not to skip.
        if List.length sceneModel.allOldBusiness > 0 then
          (sceneModel, Cmd.none)
        else
          (sceneModel, segueToDone sceneModel)
      else
        -- We have not yet received all the expected responses, so don't do anything...
        (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.oldBusinessModel
  in
    case requiredArgs sceneModel of

      (Just sessionType, Just member) ->
        if List.isEmpty sceneModel.allOldBusiness then
          blankGenericScene kioskModel
        else
          let
            tPhrase = taskPhrase sceneModel.allOldBusiness
            finish = "Finish"
            delete = "Delete"
            skipSpec = ButtonSpec "Skip" (msgForSegueToDone sessionType member) True
          in
            genericScene kioskModel
            ("You Have " ++ tPhrase ++ " In Progress!")
            "Let's Review Them"
            ( div [sceneTextStyle]
              [ vspace 25
              , text ("Select any that is already completed")
              , vspace 0
              , text "and then click 'FINISH' to fill in a timesheet"
              , vspace 0
              , text "or 'DELETE' if it was not actually worked."
              , vspace 20
              , viewOldBusinessChoices kioskModel sceneModel.allOldBusiness
              ]
            )
            ( case sceneModel.selectedItem of
              Just tcw ->
                [ ButtonSpec finish (TimeSheetPt1Vector <| TS1_Segue sessionType member tcw) True
                , ButtonSpec delete (OldBusinessVector <| OB_DeleteSelection) True
                , skipSpec
                ]
              Nothing ->
                [ ButtonSpec finish NoOp False
                , ButtonSpec delete NoOp False
                , skipSpec
                ]
            )
            []  -- Never any bad news for this scene.

      (_, _) ->
        genericScene kioskModel
        "Sorry!"
        "We've encountered an error"
        (text missingArguments)
        []
        []


viewOldBusinessChoices : KioskModel a -> List TaskClaimWork -> Html Msg
viewOldBusinessChoices kioskModel business =
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
              [viewTaskClaimWork item]
            ]
        )
        business
      )

viewTaskClaimWork : TaskClaimWork -> Html Msg
viewTaskClaimWork {task, claim} =
  let
    tDesc = task.data.shortDesc
    tDate = task.data.scheduledDate |> CD.format "%a %b %ddd" -- |> CD.superOrdinals
  in
    text <| tDesc ++ ", " ++ tDate


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
-- UTILITIES
-----------------------------------------------------------------------------

msgForSegueToDone : SessionType -> Member -> Msg
msgForSegueToDone sessionType member =
  case sessionType of
    CheckInSession -> CheckInDoneVector <| CID_Segue member
    CheckOutSession -> CheckOutDoneVector <| COD_Segue member

segueToDone : OldBusinessModel -> Cmd Msg
segueToDone sceneModel =
  case (sceneModel.sessionType, sceneModel.member) of
    (Just st, Just m) -> send <| msgForSegueToDone st m
    _ -> send <| ErrorVector <| ERR_Segue missingArguments


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
