
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
import Html exposing (Html, text, div, span, p, br)
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

type SceneState
  = AskingAboutWitness
  | AskingWitnessForId String String -- witness username and pw
  | UpdatingTimeSheet (Maybe Member)  -- the witness
  | ThankingWitness Member  -- the witness

type alias TimeSheetPt3Model =
  ----------------- Required Args:
  { sessionType : Maybe SessionType
  , member : Maybe Member
  , tcw : Maybe TaskClaimWork
  ----------------- Optional Args:
  , otherWorkDesc : Maybe String
  ---------------- Other State:
  , state : SceneState
  , badNews : List String
  }

args x =
  ( x.sessionType
  , x.member
  , x.tcw
  , x.otherWorkDesc
  )

init : Flags -> (TimeSheetPt3Model, Cmd Msg)
init flags =
  let sceneModel =
    { sessionType = Nothing
    , member = Nothing
    , tcw = Nothing
    , otherWorkDesc = Nothing
    , state = AskingAboutWitness
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

          (Just _, Just _, Just _, _) ->
            ({sceneModel | state = AskingAboutWitness}, focusOnIndex idxWitnessUsername)

          _ ->
            (sceneModel, send <| ErrorVector <| ERR_Segue missingArguments)

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
    amVisible = currentScene kioskModel == TimeSheetPt3

  in case msg of

    TS3_Segue sessionType member tcw otherWorkDesc ->
      ( { sceneModel
        | sessionType = Just sessionType
        , member = Just member
        , tcw = Just tcw
        , otherWorkDesc = otherWorkDesc
        }
      , let transition = if otherWorkDesc==Nothing then ReplaceWith else Push
        in send <| WizardVector <| transition <| TimeSheetPt3
      )

    TS3_UpdateWitnessUsername uname ->
      case sceneModel.state of
        AskingWitnessForId _ pw -> ({sceneModel | state = AskingWitnessForId uname pw}, Cmd.none)
        _ -> (sceneModel, send <| ErrorVector <| ERR_Segue programmingError)

    TS3_UpdateWitnessPassword pw ->
      case sceneModel.state of
        AskingWitnessForId uname _ -> ({sceneModel | state = AskingWitnessForId uname pw}, Cmd.none)
        _ -> (sceneModel, send <| ErrorVector <| ERR_Segue programmingError)

    TS3_NeedWitness ->
      ({sceneModel | state = AskingWitnessForId "" ""}, Cmd.none)

    TS3_WitnessCredsReady ->
      case sceneModel.state of

        AskingWitnessForId uname pw ->
          if String.isEmpty uname || String.isEmpty pw then
            ({sceneModel | badNews = ["Witness name and password must be provided."]}, Cmd.none)
          else
            let
              cmd = xis.authenticate
                (XisApi.djangoizeId uname) pw
                (TimeSheetPt3Vector << TS3_WitnessAuthResult)
            in
              (sceneModel, cmd)

        _ ->
          -- We shouldn't ever get here.
          (sceneModel, send <| ErrorVector <| ERR_Segue programmingError)

    TS3_Skipped ->
      case sceneModel.tcw of

        Nothing ->
          (sceneModel, send <| ErrorVector <| ERR_Segue missingArguments)

        Just {work} ->
          let
            -- Witness is presumably already "Nothing", but will set again anyway.
            workMod = setWorksWitness Nothing work
            -- Previous scenes may have modified work, so update it.
            cmd = xis.replaceWork workMod (TimeSheetPt3Vector << TS3_WorkUpdated)
          in
            ({sceneModel | badNews=[], state = UpdatingTimeSheet Nothing}, cmd)

    -- Order of updates is important. Update Work here, update Claim later.
    TS3_WitnessAuthResult (Ok {isAuthentic, authenticatedMember}) ->
      case sceneModel.tcw of

        Nothing ->
          (sceneModel, send <| ErrorVector <| ERR_Segue missingArguments)

        Just {work} ->
          case (isAuthentic, authenticatedMember) of

            (True, Just witness) ->
              let
                witnessUrl = xis.memberUrl witness.id
                workMod = setWorksWitness (Just witnessUrl) work
                cmd1 = xis.replaceWork workMod (TimeSheetPt3Vector << TS3_WorkUpdated)
              in
                ( { sceneModel
                  | badNews=[]
                  , state=UpdatingTimeSheet (Just witness)
                  }
                , cmd1
                )

            (True, Nothing) ->
              -- XIS shouldn't produce this so I won't trust it.
              (sceneModel, send <| ErrorVector <| ERR_Segue programmingError)

            (False, _) ->
              ({sceneModel | badNews=["Could not authenticate"]}, Cmd.none)

    -- Order of updates is important. Update Claim here, now that Work update is done.
    TS3_WorkUpdated (Ok work) ->
      case sceneModel.tcw of
        Nothing -> (sceneModel, send <| ErrorVector <| ERR_Segue missingArguments)
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
          case sceneModel.otherWorkDesc of

            Just desc ->
              ( { sceneModel | badNews = [] }
              , xis.createWorkNote
                  { author = Just claim.data.claimingMember
                  , content = desc
                  , work = (xis.workUrl work.id)
                  , whenWritten = kioskModel.currTime
                  }
                  (TimeSheetPt3Vector << TS3_WorkNoteCreated)
              )

            Nothing ->
              thankTheWitness kioskModel

        Nothing -> (sceneModel, send <| ErrorVector <| ERR_Segue missingArguments)

    TS3_WorkNoteCreated (Ok note) ->
      -- Everything worked. Scene is complete.
      thankTheWitness kioskModel

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


thankTheWitness kioskModel =
  let
    sceneModel = kioskModel.timeSheetPt3Model
  in
    case sceneModel.state of

      UpdatingTimeSheet (Just witness) ->
        ({ sceneModel | badNews = [], state=ThankingWitness witness}, Cmd.none)

      UpdatingTimeSheet Nothing ->
        ({ sceneModel | badNews = [], state=AskingAboutWitness}, popTo OldBusiness)

      _ ->
        (sceneModel, send <| ErrorVector <| ERR_Segue programmingError)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.timeSheetPt3Model
  in
    case (sceneModel.sessionType, sceneModel.member, sceneModel.tcw) of

      (Just sessionType, Just member, Just {task, claim, work}) ->
        case sceneModel.state of
          AskingAboutWitness ->
            view_IsWitnessNeeded kioskModel task claim work
          AskingWitnessForId witnessUname witnessPw ->
            view_IdentifyWitness kioskModel task claim work witnessUname witnessPw
          UpdatingTimeSheet witness ->
            blankGenericScene kioskModel
          ThankingWitness witness ->
            view_ThankWitness kioskModel witness

      _ -> errorView kioskModel missingArguments


view_IsWitnessNeeded : KioskModel a -> XisApi.Task -> XisApi.Claim -> XisApi.Work -> Html Msg
view_IsWitnessNeeded kioskModel task claim work =
  let
    sceneModel = kioskModel.timeSheetPt3Model

  in genericScene kioskModel

    "Volunteer Timesheet"
    "Do you need this work to be witnessed?"

    ( div []
      [ vspace 50
      , infoDiv kioskModel.currTime (SomeTCW <| TaskClaimWork task claim work) sceneModel.otherWorkDesc
      , vspace 70
      , p [sceneTextStyle] [text "If you want this work to apply to Work-Trade, you need to have it witnessed by a Staffer. If not, you can skip this step."]
      ]
    )

    [ ButtonSpec "Witness" (TimeSheetPt3Vector <| TS3_NeedWitness) True
    , ButtonSpec "Skip" (TimeSheetPt3Vector <| TS3_Skipped) True
    ]

    sceneModel.badNews

view_IdentifyWitness : KioskModel a -> XisApi.Task -> XisApi.Claim -> XisApi.Work -> String -> String -> Html Msg
view_IdentifyWitness kioskModel task claim work witnessUname witnessPword =
  let
    sceneModel = kioskModel.timeSheetPt3Model

  in genericScene kioskModel

    "Volunteer Timesheet"
    "Do you need this work to be witnessed?"

    ( div []
      [ vspace 50
      , infoDiv kioskModel.currTime (SomeTCW <| TaskClaimWork task claim work) sceneModel.otherWorkDesc
      , vspace 70
      , (sceneTextField kioskModel idxWitnessUsername
          "Witness Username" witnessUname
          (TimeSheetPt3Vector << TS3_UpdateWitnessUsername))
      , vspace 40
      , (scenePasswordField kioskModel idxWitnessPassword
          "Witness Password" witnessPword
          (TimeSheetPt3Vector << TS3_UpdateWitnessPassword))
      ]
    )

    [ButtonSpec "Witness" (TimeSheetPt3Vector <| TS3_WitnessCredsReady) True]
    sceneModel.badNews


view_ThankWitness : KioskModel a -> Member -> Html Msg
view_ThankWitness kioskModel witness =

  let
    sceneModel = kioskModel.timeSheetPt3Model

  in

    case (sceneModel.sessionType, sceneModel.member) of

      (Just sessionType, Just worker) ->
        genericScene kioskModel

          "Volunteer Timesheet"
          ("Thanks for Witnessing!")

          ( div [sceneTextStyle]
            [ vspace 40
            , text ("'" ++ witness.data.userName ++ "' has witnessed the work!")
            , vspace 20
            , text ("'" ++ worker.data.userName ++ "' should now continue their " ++ (sessionTypeStr sessionType) ++ ".")
            ]
          )

          [ButtonSpec "Ok" (popToMsg OldBusiness) True]
          sceneModel.badNews

      _ ->
        errorView kioskModel missingArguments


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
