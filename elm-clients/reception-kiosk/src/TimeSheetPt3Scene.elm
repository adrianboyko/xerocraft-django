
module TimeSheetPt3Scene exposing
  ( init
  , rfidWasSwiped
  , sceneWillAppear
  , update
  , view
  --------------------
  , TimeSheetPt3Model
  )

-- Standard
import Html exposing (Html, text, div, span, p)
import Html.Attributes exposing (attribute, style)
import Http exposing (header, Error(..))

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

idxTimeSheetPt3 = mdlIdBase TimeSheetPt3
idxWitnessUsername = [idxTimeSheetPt3, 1]
idxWitnessPassword = [idxTimeSheetPt3, 2]

tcwMissingStr = "Couldn't get task, claim, and work records!"

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
  , timeSheetPt3Model : TimeSheetPt3Model
  , xisSession : XisApi.Session Msg
  }


type alias TimeSheetPt3Model =
  ----------------- Args:
  { tcw : Maybe TaskClaimWork      -- REQUIRED
  , otherWorkDesc : Maybe String   -- OPTIONAL
  ---------------- Other State:
  , witnessUsername : String
  , witnessPassword : String
  , needWitness : Bool
  , badNews : List String
  }

args x =
  ( x.tcw
  , x.otherWorkDesc
  )

init : Flags -> (TimeSheetPt3Model, Cmd Msg)
init flags =
  let sceneModel =
    { tcw = Nothing
    , otherWorkDesc = Nothing
    , witnessUsername = ""
    , witnessPassword = ""
    , needWitness = False
    , badNews = []
    }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> Scene -> (TimeSheetPt3Model, Cmd Msg)
sceneWillAppear kioskModel appearing vanishing =
  let
    sceneModel = kioskModel.timeSheetPt3Model
  in
    case (appearing, vanishing) of

      (TimeSheetPt3, _) ->
        case args sceneModel of
          (Just _, _) ->
            (sceneModel, focusOnIndex idxWitnessUsername)
          _ ->
            ({sceneModel | badNews=[tcwMissingStr]}, Cmd.none)

      (_, TimeSheetPt3) ->
        -- Clear the password field when we leave this scene.
        ({sceneModel | witnessPassword=""}, Cmd.none)

      (_, _) ->
        (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : TimeSheetPt3Msg -> KioskModel a -> (TimeSheetPt3Model, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.timeSheetPt3Model
    xis = kioskModel.xisSession
    wName = sceneModel.witnessUsername
    amVisible = currentScene kioskModel == TimeSheetPt3

  in case msg of

    TS3_Segue (tcw, otherWorkDesc) ->
      ( {sceneModel | tcw = Just tcw, otherWorkDesc = otherWorkDesc}
      , let transition = if otherWorkDesc==Nothing then ReplaceWith else Push
        in send <| WizardVector <| transition <| TimeSheetPt3
      )

    TS3_UpdateWitnessUsername s ->
      ({sceneModel | witnessUsername = s}, Cmd.none)

    TS3_UpdateWitnessPassword s ->
      ({sceneModel | witnessPassword = s}, Cmd.none)

    TS3_NeedWitness ->
      ({sceneModel | needWitness=True}, Cmd.none)

    TS3_Witnessed ->
      let
        nameIsEmpty = String.isEmpty sceneModel.witnessUsername
        pwIsEmpty = String.isEmpty sceneModel.witnessPassword
      in
        if nameIsEmpty || pwIsEmpty then
          ({sceneModel | badNews = ["Witness name and password must be provided."]}, Cmd.none)
        else
          let
            cmd = xis.authenticate
              (XisApi.djangoizeId sceneModel.witnessUsername)
              sceneModel.witnessPassword
              (TimeSheetPt3Vector << TS3_WitnessAuthResult)
          in
            (sceneModel, cmd)

    TS3_Skipped ->
      case sceneModel.tcw of

        Nothing ->
          ({sceneModel | badNews=[tcwMissingStr]}, Cmd.none)

        Just {work} ->
          let
            -- Witness is presumably already "Nothing", but will set again anyway.
            workMod = setWorksWitness Nothing work
            -- Previous scenes may have modified work, so update it.
            cmd = xis.replaceWork workMod (TimeSheetPt3Vector << TS3_WorkUpdated)
          in
            ({sceneModel | badNews=[]}, cmd)

    -- Order of updates is important. Update Work here, update Claim later.
    TS3_WitnessAuthResult (Ok {isAuthentic, authenticatedMember}) ->
      case sceneModel.tcw of

        Nothing ->
          ({sceneModel | badNews=[tcwMissingStr]}, Cmd.none)

        Just {work} ->
          case (isAuthentic, authenticatedMember) of

            (True, Just witness) ->
              let
                witnessUrl = xis.memberUrl witness.id
                workMod = setWorksWitness (Just witnessUrl) work
                cmd1 = xis.replaceWork workMod (TimeSheetPt3Vector << TS3_WorkUpdated)
              in
                ({sceneModel | badNews=[]}, cmd1)

            (True, Nothing) ->
              -- XIS shouldn't produce this so I won't trust it.
              let _ = Debug.log "ERROR" "TS3_WitnessAuthResult received (True, Nothing)."
              in ({sceneModel | badNews=["Could not authenticate "++wName]}, Cmd.none)

            (False, _) ->
              ({sceneModel | badNews=["Could not authenticate "++wName]}, Cmd.none)

    -- Order of updates is important. Update Claim here, now that Work update is done.
    TS3_WorkUpdated (Ok work) ->
      case sceneModel.tcw of
        Nothing -> ({sceneModel | badNews=[tcwMissingStr]}, Cmd.none)
        Just {claim} ->
          let
            -- TODO: Task might not be done. Work might be stopping for now.
            claimMod = claim |> setClaimsStatus DoneClaimStatus
            cmd = xis.replaceClaim claimMod (TimeSheetPt3Vector << TS3_ClaimUpdated)
          in
            ({sceneModel | badNews=[]}, cmd)

    TS3_ClaimUpdated (Ok _) ->
      case sceneModel.tcw of
        Just {claim, work} ->
          ( { sceneModel | badNews = [] }
          , case sceneModel.otherWorkDesc of
            Just desc ->
              xis.createWorkNote
                { author = Just claim.data.claimingMember
                , content = desc
                , work = (xis.workUrl work.id)
                , whenWritten = kioskModel.currTime
                }
                (TimeSheetPt3Vector << TS3_WorkNoteCreated)
            Nothing ->
              popTo OldBusiness
          )
        Nothing -> ({sceneModel | badNews=[tcwMissingStr]}, Cmd.none)

    TS3_WorkNoteCreated (Ok note) ->
      -- Everything worked. Scene is complete.
      (sceneModel, popTo OldBusiness)

    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

    TS3_WitnessAuthResult (Err e) ->
      ({sceneModel | badNews=[toString e]}, Cmd.none)

    TS3_ClaimUpdated (Err e) ->
      ({sceneModel | badNews=[toString e]}, Cmd.none)

    TS3_WorkUpdated (Err e) ->
      case e of

        BadStatus response ->
          if response.status.code == 403 then
            ({sceneModel | badNews=["Bad username/password?"]}, Cmd.none)
          else
            ({sceneModel | badNews=[toString e]}, Cmd.none)

        _ ->
          ({sceneModel | badNews=[toString e]}, Cmd.none)

    TS3_WorkNoteCreated (Err e) ->
      -- Failure to create the work description is non-critical so we'll carry on to next scene.
      -- TODO: Create a backend logging facility so that failures like this can be noted via XisAPI
      (sceneModel, popTo OldBusiness)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  case kioskModel.timeSheetPt3Model.tcw of

    Just {task, claim, work} ->
      if kioskModel.timeSheetPt3Model.needWitness then
        viewWitness kioskModel task claim work
      else
        viewQuestion kioskModel task claim work

    _ -> text ""


viewQuestion : KioskModel a -> XisApi.Task -> XisApi.Claim -> XisApi.Work -> Html Msg
viewQuestion kioskModel task claim work =
  let
    sceneModel = kioskModel.timeSheetPt3Model

  in genericScene kioskModel

    "Volunteer Timesheet"
    "Do you need this work to be witnessed?"

    ( div []
      [ vspace 50
      , infoDiv kioskModel.currTime task claim work sceneModel.otherWorkDesc
      , vspace 70
      , p [sceneTextStyle] [text "If you want this work to apply to Work-Trade, you need to have it witnessed by a Staffer. If not, you can skip this step."]
      ]
    )

    [ ButtonSpec "Witness" (TimeSheetPt3Vector <| TS3_NeedWitness) True
    , ButtonSpec "Skip" (TimeSheetPt3Vector <| TS3_Skipped) True
    ]

    sceneModel.badNews

viewWitness : KioskModel a -> XisApi.Task -> XisApi.Claim -> XisApi.Work -> Html Msg
viewWitness kioskModel task claim work =
  let
    sceneModel = kioskModel.timeSheetPt3Model

  in genericScene kioskModel

    "Volunteer Timesheet"
    "Do you need this work to be witnessed?"

    ( div []
      [ vspace 50
      , infoDiv kioskModel.currTime task claim work sceneModel.otherWorkDesc
      , vspace 70
      , (sceneTextField kioskModel idxWitnessUsername
          "Witness Username" sceneModel.witnessUsername
          (TimeSheetPt3Vector << TS3_UpdateWitnessUsername))
      , vspace 40
      , (scenePasswordField kioskModel idxWitnessPassword
          "Witness Password" sceneModel.witnessPassword
          (TimeSheetPt3Vector << TS3_UpdateWitnessPassword))
      ]
    )

    [ButtonSpec "Witness" (TimeSheetPt3Vector <| TS3_Witnessed) True]

    sceneModel.badNews


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- RFID WAS SWIPED
-----------------------------------------------------------------------------

rfidWasSwiped : KioskModel a -> Result String Member -> (TimeSheetPt3Model, Cmd Msg)
rfidWasSwiped kioskModel result =
  let sceneModel = kioskModel.timeSheetPt3Model
  in case result of

    Ok m ->
      -- Reading an RFID will be considered equivalent to providing credentials, for purpose of witnessing work.
      update
        (TS3_WitnessAuthResult <| Ok <| AuthenticationResult True (Just m))
        kioskModel

    Err e ->
      ({sceneModel | badNews=[toString e]}, Cmd.none)


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------
