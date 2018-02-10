
module TimeSheetPt3Scene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , subscriptions
  , TimeSheetPt3Model
  )

-- Standard
import Html exposing (Html, text, div, span, p)
import Html.Attributes exposing (attribute, style)
import Http exposing (header, Error(..))
import Keyboard
import Char

-- Third Party
import Material
import List.Nonempty exposing (Nonempty)

-- Local
import TimeSheetCommon exposing (infoDiv)
import XisRestApi as XisApi exposing (..)
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import TimeSheetPt1Scene exposing (TimeSheetPt1Model)
import TimeSheetPt2Scene exposing (TimeSheetPt2Model)
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
workingStr = "Checking RFID!"

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
  , timeSheetPt1Model : TimeSheetPt1Model
  , timeSheetPt2Model : TimeSheetPt2Model
  , timeSheetPt3Model : TimeSheetPt3Model
  , xisSession : XisApi.Session Msg
  }


type alias TimeSheetPt3Model =
  { records : Maybe (XisApi.Task, XisApi.Claim, XisApi.Work)
  , witnessUsername : String
  , witnessPassword : String
  , digitsTyped : List Char  -- Digits that make up the RFID code
  , rfidCode : Maybe Int  -- Set immediately after all digits have been sent.
  , needWitness : Bool
  , badNews : List String
  }


init : Flags -> (TimeSheetPt3Model, Cmd Msg)
init flags =
  let sceneModel =
    { records = Nothing
    , witnessUsername = ""
    , witnessPassword = ""
    , digitsTyped = []
    , rfidCode = Nothing
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
    pt1Model = kioskModel.timeSheetPt1Model
  in
    case (appearing, vanishing) of

      (TimeSheetPt3, _) ->
        case (pt1Model.oldBusinessItem) of
          Just {task, claim, work} ->
            let
              records = Just (task, claim, work)
              newModel = {sceneModel | records=records, digitsTyped=[], rfidCode=Nothing }
            in (newModel, focusOnIndex idxWitnessUsername)
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

    -- REVIEW: Factor this out into an RFID reader helper? It's also used in ScreenSaver.
    TS3_KeyDown code ->
      if amVisible then
        case sceneModel.rfidCode of
          Nothing ->
            case code of
              13 ->
                update TS3_Witnessed kioskModel
              219 ->
                -- RFID reader is beginning to send a card number, so clear our buffer.
                ({sceneModel | digitsTyped=[]}, Cmd.none)
              221 ->
                -- RFID reader is done sending the card number, so process our buffer.
                handleRfid kioskModel
              c ->
                if c>=48 && c<=57 then
                  -- A digit, presumably in the RFID's number. '0' = code 48, '9' = code 57.
                  let updatedDigits = Char.fromCode c :: sceneModel.digitsTyped
                  in ({sceneModel | digitsTyped = updatedDigits }, Cmd.none)
                else
                  -- Unexpected code.
                  (sceneModel, Cmd.none)
          Just _ ->
            ({sceneModel | witnessUsername = workingStr }, Cmd.none)
      else
        -- Scene is not visible.
        (sceneModel, Cmd.none)

    TS3_WitnessListResult (Ok {results}) ->
      -- ASSERTION: There should be exactly one witness in results.
      case List.head results of
        Just w ->
          -- Reading an RFID will be considered equivalent to providing credentials, for purpose of witnessing work.
          let
            sModel = {sceneModel | witnessUsername=w.data.userName}
            kModel = {kioskModel | timeSheetPt3Model = sModel }
            synthMsg = TS3_WitnessAuthResult <| Ok <| AuthenticationResult True (Just w)
          in update synthMsg kModel
        Nothing ->
          ({sceneModel | witnessUsername="", badNews=["RFID not registered."]}, Cmd.none)

    TS3_UpdateWitnessUsername s ->
      ({sceneModel | witnessUsername = XisApi.djangoizeId s}, Cmd.none)

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
              sceneModel.witnessUsername
              sceneModel.witnessPassword
              (TimeSheetPt3Vector << TS3_WitnessAuthResult)
          in
            (sceneModel, cmd)

    TS3_Skipped ->
      case sceneModel.records of

        Nothing ->
          ({sceneModel | badNews=[tcwMissingStr]}, Cmd.none)

        Just (_, _, work) ->
          let
            -- Witness is presumably already "Nothing", but will set again anyway.
            workMod = setWorksWitness Nothing work
            -- Previous scenes may have modified work, so update it.
            cmd = xis.replaceWork workMod (TimeSheetPt3Vector << TS3_WorkUpdated)
          in
            ({sceneModel | badNews=[]}, cmd)

    -- Order of updates is important. Update Work here, update Claim later.
    TS3_WitnessAuthResult (Ok {isAuthentic, authenticatedMember}) ->
      case sceneModel.records of

        Nothing ->
          ({sceneModel | badNews=[tcwMissingStr]}, Cmd.none)

        Just (_, _, work) ->
          case (isAuthentic, authenticatedMember) of

            (True, Just witness) ->
              let
                witnessUrl = xis.memberUrl witness.id
                workMod = setWorksWitness (Just witnessUrl) work
                cmd1 = xis.replaceWork workMod (TimeSheetPt3Vector << TS3_WorkUpdated)
                cmd2 = xis.createVisitEvent
                         { who=witnessUrl
                         , when=kioskModel.currTime
                         , eventType=VET_Present
                         , method=VEM_FrontDesk
                         , reason=Nothing
                         }
                         (TimeSheetPt3Vector << TS3_WitnessPresentResult)
              in
                ({sceneModel | badNews=[]}, Cmd.batch [cmd1, cmd2])

            (True, Nothing) ->
              -- XIS shouldn't produce this so I won't trust it.
              let _ = Debug.log "ERROR" "TS3_WitnessAuthResult received (True, Nothing)."
              in ({sceneModel | badNews=["Could not authenticate "++wName]}, Cmd.none)

            (False, _) ->
              ({sceneModel | badNews=["Could not authenticate "++wName]}, Cmd.none)

    -- Order of updates is important. Update Claim here, now that Work update is done.
    TS3_WorkUpdated (Ok work) ->
      case sceneModel.records of
        Nothing -> ({sceneModel | badNews=[tcwMissingStr]}, Cmd.none)
        Just (_, c, _) ->
          let
            -- TODO: Task might not be done. Work might be stopping for now.
            claimMod = c |> setClaimsStatus DoneClaimStatus
            cmd = xis.replaceClaim claimMod (TimeSheetPt3Vector << TS3_ClaimUpdated)
          in
            ({sceneModel | badNews=[]}, cmd)

    TS3_ClaimUpdated (Ok claim) ->
      case sceneModel.records of
        Nothing -> ({sceneModel | badNews=[tcwMissingStr]}, Cmd.none)
        Just (_, c, w) ->
          let
            pt2Model = kioskModel.timeSheetPt2Model
            noteData = XisApi.WorkNoteData
              (Just c.data.claimingMember)
              pt2Model.otherWorkDesc
              (xis.workUrl w.id)
              kioskModel.currTime
            cmd = if String.length pt2Model.otherWorkDesc > 0
              then xis.createWorkNote noteData (TimeSheetPt3Vector << TS3_WorkNoteCreated)
              else (popTo OldBusiness)
          in
            ({sceneModel | badNews=[]}, cmd)

    TS3_WorkNoteCreated (Ok note) ->
      -- Everything worked. Scene is complete.
      (sceneModel, popTo OldBusiness)

    TS3_WitnessPresentResult (Ok _) ->
      -- Don't need to do anything when this succeeds.
      (sceneModel, Cmd.none)

    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

    TS3_WitnessListResult (Err e) ->
      ( { sceneModel
        | badNews=[toString e]
        , rfidCode=Nothing
        , digitsTyped=[]
        }
      , Cmd.none
      )

    TS3_WitnessAuthResult (Err e) ->
      ({sceneModel | badNews=[toString e]}, Cmd.none)

    TS3_ClaimUpdated (Err e) ->
      ({sceneModel | badNews=[toString e]}, Cmd.none)

    TS3_WitnessPresentResult (Err e) ->
      let
        _ = Debug.log "TS3 ERR" (toString e)
      in
        (sceneModel, Cmd.none)

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
      (sceneModel, segueTo TimeSheetPt1)


handleRfid : KioskModel a -> (TimeSheetPt3Model, Cmd Msg)
handleRfid kioskModel =
  let
    sceneModel = kioskModel.timeSheetPt3Model
    xis = kioskModel.xisSession
  in
    case sceneModel.rfidCode of

      Just _ ->
        -- We're already in the process of checking a code, so ignore this one.
        -- It's presumably the same code anyway, since the reader reads multiple times.
        ( {sceneModel | witnessUsername=workingStr}
        , Cmd.none
        )

      Nothing ->
        let
          rfidNumber = List.reverse sceneModel.digitsTyped |> String.fromList |> String.toInt
          filter = Result.map RfidNumberEquals rfidNumber
        in
          case (rfidNumber, filter) of

            (Ok n, Ok f) ->
              ( {sceneModel | rfidCode=Just n, witnessUsername=workingStr}
              , xis.listMembers [f] (TimeSheetPt3Vector << TS3_WitnessListResult)
              )

            (Err e, _) ->
              ( {sceneModel | rfidCode=Nothing, witnessUsername="", badNews=[toString e]}
              , Cmd.none
              )

            (_, Err e) ->
              ( {sceneModel | rfidCode=Nothing, witnessUsername="", badNews=[toString e]}
              , Cmd.none
              )


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  case kioskModel.timeSheetPt3Model.records of

    Just (t, c, w) ->
      if kioskModel.timeSheetPt3Model.needWitness then
        viewWitness kioskModel t c w
      else
        viewQuestion kioskModel t c w

    _ -> text ""


viewQuestion : KioskModel a -> XisApi.Task -> XisApi.Claim -> XisApi.Work -> Html Msg
viewQuestion kioskModel task claim work =
  let
    sceneModel = kioskModel.timeSheetPt3Model
    pt2Model = kioskModel.timeSheetPt2Model
    otherWorkDesc =
      if String.isEmpty pt2Model.otherWorkDesc
        then Nothing
        else Just pt2Model.otherWorkDesc

  in genericScene kioskModel

    "Volunteer Timesheet"
    "Do you need this work to be witnessed?"

    ( div []
      [ vspace 50
      , infoDiv kioskModel.currTime task claim work otherWorkDesc
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
    pt2Model = kioskModel.timeSheetPt2Model
    otherWorkDesc =
      if String.isEmpty pt2Model.otherWorkDesc
        then Nothing
        else Just pt2Model.otherWorkDesc

  in genericScene kioskModel

    "Volunteer Timesheet"
    "Do you need this work to be witnessed?"

    ( div []
      [ vspace 50
      , infoDiv kioskModel.currTime task claim work otherWorkDesc
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

subscriptions: KioskModel a -> Sub Msg
subscriptions kioskModel =
    if currentScene kioskModel == TimeSheetPt3 then
      Keyboard.downs (TimeSheetPt3Vector << TS3_KeyDown)
    else
      Sub.none


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------
