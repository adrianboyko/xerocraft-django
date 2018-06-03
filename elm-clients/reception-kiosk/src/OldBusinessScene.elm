
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
  , currentBusiness : Maybe Business
  ---------------- Other State:
  , allOldBusiness : List Business
  , selectedBusiness : Maybe Business
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
    , currentBusiness = Nothing
    ---------------- Other State:
    , allOldBusiness = []
    , selectedBusiness = Nothing
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
    cmd1 = kioskModel.xisSession.listClaims
      [ ClaimingMemberEquals <| memberId kioskModel
      , ClaimStatusEquals WorkingClaimStatus
      ]
      (OldBusinessVector << OB_WorkingClaimsResult)
    cmd2 = kioskModel.xisSession.listPlays
      [ PlayingMemberEquals <| memberId kioskModel
      , PlayDurationIsNull True
      ]
      (OldBusinessVector << OB_OpenPlaysResult)
  in
    ( { sceneModel
      | allOldBusiness=[]
      , selectedBusiness=Nothing
      , workResponsesExpected=Nothing -- We'll know when we get the claims.
      , workResponsesReceived=0
      }
    , Cmd.batch [cmd1, cmd2]
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

      OB_SegueA sessionType member ->
        ( {sceneModel | sessionType = Just sessionType, member = Just member}
        , send <| WizardVector <| Push <| OldBusiness
        )

      OB_SegueB sessionType member currentBusiness ->
        ( { sceneModel
          | sessionType = Just sessionType
          , member = Just member
          , currentBusiness = Just currentBusiness
          }
        , send <| WizardVector <| Push <| OldBusiness
        )

      -- This case starts the lookup of tasks corresponding to the open claims.
      OB_WorkingClaimsResult (Ok {results}) ->
        let
          -- We don't want the business that the user just started, if any.
          claims = case sceneModel.currentBusiness of
            Just (SomeTCW tcw) -> List.filter (\x -> x.id /= tcw.claim.id) results
            Just (SomePlay p) -> results
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
          allOldBusinessPlus = SomeTCW (TaskClaimWork task claim work) :: sceneModel.allOldBusiness
          newCount = sceneModel.workResponsesReceived + 1
          newSceneModel = case work.data.workDuration of
            Nothing -> {sceneModel | allOldBusiness=allOldBusinessPlus, workResponsesReceived=newCount}
            Just _ -> {sceneModel | workResponsesReceived=newCount}
        in
          considerSkip newSceneModel

      OB_DeleteSelection ->
        case sceneModel.selectedBusiness of

          Just (SomeTCW {task, claim, work}) ->
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
              newModel = {sceneModel | selectedBusiness=Nothing }
            in
              (newModel, Cmd.batch [cmd1, cmd2])

          Just (SomePlay p) ->
            ( sceneModel
            , xis.deletePlayById p.id (OldBusinessVector << OB_NotePlayDeleted)
            )

          Nothing ->
            -- Shouldn't get here since there must be a selction in order to click "DELETE"
            (sceneModel, Cmd.none)

      OB_NoteClaimUpdated (Ok _) ->
        -- No action required.
        (sceneModel, Cmd.none)

      OB_NoteWorkDeleted _ ->
        checkForOldBusiness kioskModel

      OB_ToggleItem item ->
        ({sceneModel | selectedBusiness = Just item}, Cmd.none)

      OB_OpenPlaysResult (Ok {results}) ->
        let
          -- We don't want the business that the user just started, if any.
          plays = case sceneModel.currentBusiness of
            Just (SomePlay p) -> List.filter (\x -> x.id /= p.id) results
            Just (SomeTCW _) -> results
            Nothing -> results
          someOldBusiness = sceneModel.allOldBusiness
          moreOldBusiness = List.map SomePlay plays
        in
          ( {sceneModel | allOldBusiness = List.append someOldBusiness moreOldBusiness}
          , Cmd.none
          )

      OB_NotePlayDeleted (Ok _) ->
        checkForOldBusiness kioskModel

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

      OB_OpenPlaysResult (Err error) ->
        let _ = Debug.log "WARNING" (toString error)
        in (sceneModel, Cmd.none)

      OB_NotePlayDeleted (Err error) ->
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
            finish = "Log"
            delete = "Delete"
            skipSpec = ButtonSpec "Skip" (msgForSegueToDone sessionType member) True
          in
            genericScene kioskModel
            "We Need Some Info From You"
            "(to update your hours balance)"
            ( div [sceneTextStyle]
              [ vspace 25
              , text ("Select an item below then click 'LOG' to fill in a timesheet.")
              , vspace 40
              , viewOldBusinessChoices kioskModel sceneModel.allOldBusiness
              ]
            )
            ( case sceneModel.selectedBusiness of
              Just (SomeTCW tcw) ->
                [ ButtonSpec finish (TimeSheetPt1Vector <| TS1_Segue sessionType member (SomeTCW tcw)) True
                , ButtonSpec delete (OldBusinessVector <| OB_DeleteSelection) True
                , skipSpec
                ]
              Just (SomePlay play) ->
                [ ButtonSpec finish (TimeSheetPt1Vector <| TS1_Segue sessionType member (SomePlay play)) True
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


viewOldBusinessChoices : KioskModel a -> List Business -> Html Msg
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
                (case sceneModel.selectedBusiness of
                  Just (SomeTCW tcw) -> SomeTCW tcw == item
                  Just (SomePlay p) -> SomePlay p == item
                  Nothing -> False
                )
              , Options.onToggle (OldBusinessVector <| OB_ToggleItem <| item)
              ]
              [viewBusiness item]
            ]
        )
        business
      )


viewBusiness : Business -> Html Msg
viewBusiness business =
  case business of
    SomeTCW tcw -> viewTCW tcw
    SomePlay p -> viewPlay p


viewTCW : TaskClaimWork -> Html Msg
viewTCW {task, claim} =
  let
    tDesc = task.data.shortDesc
    tDate = task.data.scheduledDate |> CD.format "%a %b %ddd" -- |> CD.superOrdinals
  in
    text <| tDesc ++ ", " ++ tDate


viewPlay : Play -> Html Msg
viewPlay play =
  let
    tDate = play.data.playDate |> CD.format "%a %b %ddd" -- |> CD.superOrdinals
  in
    text <| "Membership Privileges, " ++ tDate


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
