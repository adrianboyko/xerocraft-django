port module ReceptionKiosk exposing (..)

-- Standard
import Html exposing (Html, Attribute, a, div, text, span, button, br, p, img, h1, h2, ol, li, b, canvas)
import Html.Attributes exposing (style, src, id, tabindex, width, height)
import Regex exposing (regex)
import Http
import Time exposing (Time, second)
import Task

-- Third party
import List.Nonempty as Nonempty exposing (Nonempty)
import List.Extra as ListX
import Material

-- Local
import Types exposing (..)
import AuthorizeEntryScene
import BuyMembershipScene
import CheckInScene
import CheckInDoneScene
import CheckOutScene
import CheckOutDoneScene
import CreatingAcctScene
import EmailInUseScene
import ErrorScene
import HowDidYouHearScene
import NewMemberScene
import NewUserScene
import OldBusinessScene
import PublicHoursScene
import ReasonForVisitScene
import RfidHelper
import StartScene
import SignUpDoneScene
import TaskListScene
import TimeSheetPt1Scene
import TimeSheetPt2Scene
import TimeSheetPt3Scene
import TaskInfoScene
import UseBankedHoursScene
import WaiverScene
import WelcomeForRfidScene
import WelcomeScene
import YouCantEnterScene

import DjangoRestFramework as DRF
import XisRestApi as XisApi
import MembersApi as MembersApi
import Duration exposing (Duration)


-----------------------------------------------------------------------------
-- MAIN
-----------------------------------------------------------------------------

main =
  Html.programWithFlags
    { init = init
    , view = view
    , update = update
    , subscriptions = subscriptions
    }


-----------------------------------------------------------------------------
-- PORTS
-----------------------------------------------------------------------------

{-| Sets focus on the element with the given id but ONLY IF there is NOT
an element that already has focus. Since scenes appear with no default
focus, use this to set one. This will also showKeyboard().
-}
port setFocusIfNoFocus : String -> Cmd msg

{-| This port is for asynchronous result information from setFocusIfNoFocus.
If focus is successfully set, a True will be sent back via this port, else
a False will be sent.
-}
port focusWasSet : (Bool -> msg) -> Sub msg


-----------------------------------------------------------------------------
-- MODEL
-----------------------------------------------------------------------------

type alias Model =
  { flags : Flags
  , currTime : Time
  , timeShift : Duration  -- For testing. Will always be 0 unless server is on dev host.
  , sceneStack : Nonempty Scene -- 1st element is the top of the stack
  , idxToFocus : Maybe (List Int)  -- Can't use Material.Component.Index (https://github.com/debois/elm-mdl/issues/342)
  -- elm-mdl model:
  , mdl : Material.Model
  -- api models:
  , xisSession : XisApi.Session Msg
  , membersApi : MembersApi.Session Msg
  -- rfid helper model:
  , rfidHelperModel : RfidHelper.RfidHelperModel
  -- Scene models:
  , authorizeEntryModel  : AuthorizeEntryScene.AuthorizeEntryModel
  , buyMembershipModel   : BuyMembershipScene.BuyMembershipModel
  , checkInModel         : CheckInScene.CheckInModel
  , checkInDoneModel     : CheckInDoneScene.CheckInDoneModel
  , checkOutModel        : CheckOutScene.CheckOutModel
  , checkOutDoneModel    : CheckOutDoneScene.CheckOutDoneModel
  , creatingAcctModel    : CreatingAcctScene.CreatingAcctModel
  , emailInUseModel      : EmailInUseScene.EmailInUseModel
  , errorModel           : ErrorScene.ErrorModel
  , howDidYouHearModel   : HowDidYouHearScene.HowDidYouHearModel
  , signUpDoneModel      : SignUpDoneScene.SignUpDoneModel
  , startModel           : StartScene.StartModel
  , newMemberModel       : NewMemberScene.NewMemberModel
  , newUserModel         : NewUserScene.NewUserModel
  , oldBusinessModel     : OldBusinessScene.OldBusinessModel
  , publicHoursModel     : PublicHoursScene.PublicHoursModel
  , reasonForVisitModel  : ReasonForVisitScene.ReasonForVisitModel
  , taskInfoModel        : TaskInfoScene.TaskInfoModel
  , taskListModel        : TaskListScene.TaskListModel
  , timeSheetPt1Model    : TimeSheetPt1Scene.TimeSheetPt1Model
  , timeSheetPt2Model    : TimeSheetPt2Scene.TimeSheetPt2Model
  , timeSheetPt3Model    : TimeSheetPt3Scene.TimeSheetPt3Model
  , useBankedHoursModel  : UseBankedHoursScene.UseBankedHoursModel
  , waiverModel          : WaiverScene.WaiverModel
  , welcomeForRfidModel  : WelcomeForRfidScene.WelcomeForRfidModel
  , welcomeModel         : WelcomeScene.WelcomeModel
  , youCantEnterModel    : YouCantEnterScene.YouCantEnterModel
  }

init : Flags -> (Model, Cmd Msg)
init f =
  let
    (authorizeEntryModel,  authorizeEntryCmd ) = AuthorizeEntryScene.init  f
    (buyMembershipModel,   buyMembershipCmd  ) = BuyMembershipScene.init   f
    (checkInModel,         checkInCmd        ) = CheckInScene.init         f
    (checkInDoneModel,     checkInDoneCmd    ) = CheckInDoneScene.init     f
    (checkOutModel,        checkOutCmd       ) = CheckOutScene.init        f
    (checkOutDoneModel,    checkOutDoneCmd   ) = CheckOutDoneScene.init    f
    (creatingAcctModel,    creatingAcctCmd   ) = CreatingAcctScene.init    f
    (emailInUseModel,      emailInUseCmd     ) = EmailInUseScene.init      f
    (errorModel,           errorCmd          ) = ErrorScene.init           f
    (howDidYouHearModel,   howDidYouHearCmd  ) = HowDidYouHearScene.init   f
    (newMemberModel,       newMemberCmd      ) = NewMemberScene.init       f
    (newUserModel,         newUserCmd        ) = NewUserScene.init         f
    (oldBusinessModel,     oldBusinessCmd    ) = OldBusinessScene.init     f
    (publicHoursModel,     publicHoursCmd    ) = PublicHoursScene.init     f
    (reasonForVisitModel,  reasonForVisitCmd ) = ReasonForVisitScene.init  f
    (signUpDoneModel,      signUpDoneCmd     ) = SignUpDoneScene.init      f
    (startModel,           startCmd          ) = StartScene.init           f
    (taskInfoModel,        taskInfoCmd       ) = TaskInfoScene.init        f
    (taskListModel,        taskListCmd       ) = TaskListScene.init        f
    (timeSheetPt1Model,    timeSheetPt1Cmd   ) = TimeSheetPt1Scene.init    f
    (timeSheetPt2Model,    timeSheetPt2Cmd   ) = TimeSheetPt2Scene.init    f
    (timeSheetPt3Model,    timeSheetPt3Cmd   ) = TimeSheetPt3Scene.init    f
    (useBankedHoursModel,  useBankedHoursmd  ) = UseBankedHoursScene.init  f
    (waiverModel,          waiverCmd         ) = WaiverScene.init          f
    (welcomeForRfidModel,  welcomeForRfidCmd ) = WelcomeForRfidScene.init  f
    (welcomeModel,         welcomeCmd        ) = WelcomeScene.init         f
    (youCantEnterModel,    youCantEnterCmd   ) = YouCantEnterScene.init    f
    model =
      { flags = f
      , currTime = 0
      , timeShift = f.timeShift
      , sceneStack = Nonempty.fromElement Start
      , idxToFocus = Nothing
      , mdl = Material.model
      , xisSession = XisApi.createSession f.xisApiFlags (DRF.Token f.uniqueKioskId)
      , membersApi = MembersApi.createSession f.membersApiFlags
      , rfidHelperModel = RfidHelper.create RfidWasSwiped
      -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
      , authorizeEntryModel  = authorizeEntryModel
      , buyMembershipModel   = buyMembershipModel
      , checkInModel         = checkInModel
      , checkInDoneModel     = checkInDoneModel
      , checkOutModel        = checkOutModel
      , checkOutDoneModel    = checkOutDoneModel
      , creatingAcctModel    = creatingAcctModel
      , emailInUseModel      = emailInUseModel
      , errorModel           = errorModel
      , howDidYouHearModel   = howDidYouHearModel
      , newMemberModel       = newMemberModel
      , newUserModel         = newUserModel
      , oldBusinessModel     = oldBusinessModel
      , publicHoursModel     = publicHoursModel
      , reasonForVisitModel  = reasonForVisitModel
      , signUpDoneModel      = signUpDoneModel
      , startModel           = startModel
      , taskInfoModel        = taskInfoModel
      , taskListModel        = taskListModel
      , timeSheetPt1Model    = timeSheetPt1Model
      , timeSheetPt2Model    = timeSheetPt2Model
      , timeSheetPt3Model    = timeSheetPt3Model
      , useBankedHoursModel  = useBankedHoursModel
      , waiverModel          = waiverModel
      , welcomeForRfidModel  = welcomeForRfidModel
      , welcomeModel         = welcomeModel
      , youCantEnterModel    = youCantEnterModel
      }
    cmds =
      [ authorizeEntryCmd
      , buyMembershipCmd
      , checkInCmd
      , checkInDoneCmd
      , checkOutCmd
      , checkOutDoneCmd
      , creatingAcctCmd
      , emailInUseCmd
      , errorCmd
      , howDidYouHearCmd
      , newMemberCmd
      , newUserCmd
      , publicHoursCmd
      , reasonForVisitCmd
      , startCmd
      , taskInfoCmd
      , taskListCmd
      , timeSheetPt1Cmd
      , timeSheetPt2Cmd
      , timeSheetPt3Cmd
      , waiverCmd
      , welcomeForRfidCmd
      , welcomeCmd
      , youCantEnterCmd
      ]
  in
    (model, Cmd.batch cmds)


-----------------------------------------------------------------------------
-- RESET
-----------------------------------------------------------------------------

-- reset restores the model as it was after init.
reset : Model -> (Model, Cmd Msg)
reset m =
  init m.flags


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
  case msg of

    NoOp ->
      (model, Cmd.none)

    IgnoreResultHttpErrorString _ ->
      (model, Cmd.none)

    RfidWasSwiped result ->
      case Nonempty.head model.sceneStack of

        Start ->
          let (newMod, cmd) = StartScene.rfidWasSwiped model result
          in ({model | startModel = newMod}, cmd)

        CheckIn ->
          let (newMod, cmd) = CheckInScene.rfidWasSwiped model result
          in ({model | checkInModel = newMod}, cmd)

        CheckOut ->
          let (newMod, cmd) = CheckOutScene.rfidWasSwiped model result
          in ({model | checkOutModel = newMod}, cmd)

        TimeSheetPt3 ->
          let (newMod, cmd) = TimeSheetPt3Scene.rfidWasSwiped model result
          in ({model | timeSheetPt3Model = newMod}, cmd)

        _ -> (model, Cmd.none)

    RfidHelperVector msg ->
      let (rhMod, rhCmd) = RfidHelper.update msg model
      in ({model | rfidHelperModel=rhMod }, rhCmd)

    WizardVector wizMsg ->
      let currScene = Nonempty.head model.sceneStack
      in case wizMsg of
        Push nextScene ->
          -- Push the new scene onto the scene stack.
          let
            newModel = {model | sceneStack = Nonempty.cons nextScene model.sceneStack }
          in
            update (WizardVector <| (SceneWillAppear nextScene currScene)) newModel

        Pop ->
          -- Pop the top scene off the stack.
          let
            newModel = {model | sceneStack = Nonempty.pop model.sceneStack }
            newScene = Nonempty.head newModel.sceneStack
          in
            update (WizardVector <| (SceneWillAppear newScene currScene)) newModel

        PopTo scene ->
          let
            toBePopped = ListX.takeWhile ((/=) scene) (Nonempty.toList model.sceneStack)
            popCmds = List.repeat (List.length toBePopped) (send <| WizardVector <| Pop)
          in
            (model, Cmd.batch popCmds)

        Rebase ->
          -- Resets the stack so that top item becomes ONLY item. Prevents BACK.
          let
            newStack = Nonempty.dropTail model.sceneStack
            newModel = {model | sceneStack = newStack }
          in
            (newModel, Cmd.none)

        RebaseTo scene ->  -- This code might seem strange b/c stack is type List.Nonempty, NOT List.
          if Nonempty.get 1 model.sceneStack == scene then
            -- We've reached the desired state.  ("get 1" gets the 2nd item)
            (model, Cmd.none)
          else if Nonempty.length model.sceneStack == 2 then
            -- Indicates a programming error as we shouldn't have exhausted the tail looking for the scene.
            let _ = Debug.log "RebaseTo couldn't find: " scene
            in (model, Cmd.none)
          else
            -- Recursive step:
            let
              head = Nonempty.head model.sceneStack
              newTail = model.sceneStack |> Nonempty.pop |> Nonempty.pop
              newSceneStack = Nonempty.cons head newTail
            in
              update (WizardVector <| RebaseTo <| scene) {model | sceneStack=newSceneStack}

        ReplaceWith scene ->
          let
            newSceneStack = model.sceneStack |> Nonempty.pop
          in
            update (WizardVector <| Push <| scene) {model | sceneStack=newSceneStack}

        Reset -> reset model

        SceneWillAppear appearing vanishing ->
          -- REVIEW: Standardize so that every scene gets both appearing and vanishing?
          let
            -- REVIEW: It's too easy to forget to add these.
            (mCI,  cCI)  = CheckInScene.sceneWillAppear model appearing
            (mCO,  cCO)  = CheckOutScene.sceneWillAppear model appearing
            (mCOD, cCOD) = CheckOutDoneScene.sceneWillAppear model appearing vanishing
            (mCA,  cCA)  = CreatingAcctScene.sceneWillAppear model appearing
            (mERR, cERR) = ErrorScene.sceneWillAppear model appearing vanishing
            (mHD,  cHD)  = HowDidYouHearScene.sceneWillAppear model appearing
            (mNM,  cNM)  = NewMemberScene.sceneWillAppear model appearing
            (mNU,  cNU)  = NewUserScene.sceneWillAppear model appearing
            (mOB,  cOB)  = OldBusinessScene.sceneWillAppear model appearing vanishing
            (mR4V, cR4V) = ReasonForVisitScene.sceneWillAppear model appearing vanishing
            (mRH,  cRH)  = RfidHelper.sceneWillAppear model appearing vanishing
            (mSUD, cSUD) = SignUpDoneScene.sceneWillAppear model appearing vanishing
            (mSS,  cSS)  = StartScene.sceneWillAppear model appearing
            (mTI,  cTI)  = TaskInfoScene.sceneWillAppear model appearing vanishing
            (mTL,  cTL)  = TaskListScene.sceneWillAppear model appearing vanishing
            (mTS1, cTS1) = TimeSheetPt1Scene.sceneWillAppear model appearing vanishing
            (mTS2, cTS2) = TimeSheetPt2Scene.sceneWillAppear model appearing vanishing
            (mTS3, cTS3) = TimeSheetPt3Scene.sceneWillAppear model appearing vanishing
            (mW,   cW)   = WaiverScene.sceneWillAppear model appearing
            newModel =
              -- REVIEW: It's too easy to forget to add these.
              { model
              | idxToFocus = Nothing
              , checkInModel = mCI
              , checkOutModel = mCO
              , checkOutDoneModel = mCOD
              , creatingAcctModel = mCA
              , errorModel = mERR
              , howDidYouHearModel = mHD
              , newMemberModel = mNM
              , newUserModel = mNU
              , oldBusinessModel = mOB
              , reasonForVisitModel = mR4V
              , rfidHelperModel = mRH
              , signUpDoneModel = mSUD
              , startModel = mSS
              , taskInfoModel = mTI
              , taskListModel = mTL
              , timeSheetPt1Model = mTS1
              , timeSheetPt2Model = mTS2
              , timeSheetPt3Model = mTS3
              , waiverModel = mW
              }
          in
            (newModel, Cmd.batch
              -- REVIEW: It's too easy to forget to add these.
              [ cCI, cCO, cCOD, cCA, cERR, cHD, cNM, cNU, cOB
              , cRH, cR4V, cSS, cSUD, cTI, cTL, cTS1, cTS2, cTS3, cW
              ]
            )

        Tick time ->
          let
            (mCA, cCA) = CreatingAcctScene.tick time model
            (mCI, cCI) = CheckInScene.tick time model
            (mRH, cRH) = RfidHelper.tick time model
            (mSS, cSS) = StartScene.tick time model
            newModel =
              { model
              | currTime = time + model.timeShift * Duration.ticksPerSecond
              , creatingAcctModel = mCA
              , checkInModel = mCI
              , rfidHelperModel = mRH
              , startModel = mSS
              }
            focusCmd =
              case model.idxToFocus of
                Just idx -> idx |> toString |> setFocusIfNoFocus  -- Send to port
                Nothing -> Cmd.none
          in
            (newModel, Cmd.batch [focusCmd, cCA, cCI, cRH, cSS])

        FocusOnIndex idx ->
          let
            -- REVIEW: Why did previous version always also check && List.isEmpty model.badNews
            focusCmd = idx |> toString |> setFocusIfNoFocus  -- Send to port
            newModel = {model | idxToFocus=Just idx}
          in
            (newModel, focusCmd)

        FocusWasSet wasSet ->
          if wasSet then
            ({model | idxToFocus=Nothing}, Cmd.none)
          else
            (model, Cmd.none)

    AuthorizeEntryVector x ->
      let (sm, cmd) = AuthorizeEntryScene.update x model
      in ({model | authorizeEntryModel = sm}, cmd)

    BuyMembershipVector x ->
      let (sm, cmd) = BuyMembershipScene.update x model
      in ({model | buyMembershipModel = sm}, cmd)

    CheckInDoneVector x ->
      let (sm, cmd) = CheckInDoneScene.update x model
      in ({model | checkInDoneModel = sm}, cmd)

    CheckInVector x ->
      let (sm, cmd) = CheckInScene.update x model
      in ({model | checkInModel = sm}, cmd)

    CheckOutDoneVector x ->
      let (sm, cmd) = CheckOutDoneScene.update x model
      in ({model | checkOutDoneModel = sm}, cmd)

    CheckOutVector x ->
      let (sm, cmd) = CheckOutScene.update x model
      in ({model | checkOutModel = sm}, cmd)

    CreatingAcctVector x ->
      let (sm, cmd) = CreatingAcctScene.update x model
      in ({model | creatingAcctModel = sm}, cmd)

    EmailInUseVector x ->
      let (sm, cmd) = EmailInUseScene.update x model
      in ({model | emailInUseModel = sm}, cmd)

    ErrorVector x ->
      let (sm, cmd) = ErrorScene.update x model
      in ({model | errorModel = sm}, cmd)

    HowDidYouHearVector x ->
      let (sm, cmd) = HowDidYouHearScene.update x model
      in ({model | howDidYouHearModel = sm}, cmd)

    NewMemberVector x ->
      let (sm, cmd) = NewMemberScene.update x model
      in ({model | newMemberModel = sm}, cmd)

    NewUserVector x ->
      let (sm, cmd) = NewUserScene.update x model
      in ({model | newUserModel = sm}, cmd)

    OldBusinessVector x ->
      let (sm, cmd) = OldBusinessScene.update x model
      in ({model | oldBusinessModel = sm}, cmd)

    PublicHoursVector x ->
      let (sm, cmd) = PublicHoursScene.update x model
      in ({model | publicHoursModel = sm}, cmd)

    ReasonForVisitVector x ->
      let (sm, cmd) = ReasonForVisitScene.update x model
      in ({model | reasonForVisitModel = sm}, cmd)

    SignUpDoneVector x ->
      let (sm, cmd) = SignUpDoneScene.update x model
      in ({model | signUpDoneModel = sm}, cmd)

    StartVector x ->
      let (sm, cmd) = StartScene.update x model
      in ({model | startModel = sm}, cmd)

    TaskInfoVector x ->
      let (sm, cmd) = TaskInfoScene.update x model
      in ({model | taskInfoModel = sm}, cmd)

    TaskListVector x ->
      let (sm, cmd) = TaskListScene.update x model
      in ({model | taskListModel = sm}, cmd)

    TimeSheetPt1Vector x ->
      let (sm, cmd) = TimeSheetPt1Scene.update x model
      in ({model | timeSheetPt1Model = sm}, cmd)

    TimeSheetPt2Vector x ->
      let (sm, cmd) = TimeSheetPt2Scene.update x model
      in ({model | timeSheetPt2Model = sm}, cmd)

    TimeSheetPt3Vector x ->
      let (sm, cmd) = TimeSheetPt3Scene.update x model
      in ({model | timeSheetPt3Model = sm}, cmd)

    UseBankedHoursVector x ->
      let (sm, cmd) = UseBankedHoursScene.update x model
      in ({model | useBankedHoursModel = sm}, cmd)

    WaiverVector x ->
      let (sm, cmd) = WaiverScene.update x model
      in ({model | waiverModel = sm}, cmd)

    WelcomeForRfidVector x ->
      let (sm, cmd) = WelcomeForRfidScene.update x model
      in ({model | welcomeForRfidModel = sm}, cmd)

    YouCantEnterVector x ->
      let (sm, cmd) = YouCantEnterScene.update x model
      in ({model | youCantEnterModel = sm}, cmd)

    MdlVector x ->
      Material.update MdlVector x model


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : Model -> Html Msg
view model =
  let currScene = Nonempty.head model.sceneStack
  in case currScene of
    AuthorizeEntry  -> AuthorizeEntryScene.view  model
    BuyMembership   -> BuyMembershipScene.view   model
    CheckIn         -> CheckInScene.view         model
    CheckInDone     -> CheckInDoneScene.view     model
    CheckOut        -> CheckOutScene.view        model
    CheckOutDone    -> CheckOutDoneScene.view    model
    CreatingAcct    -> CreatingAcctScene.view    model
    EmailInUse      -> EmailInUseScene.view      model
    Error           -> ErrorScene.view           model
    HowDidYouHear   -> HowDidYouHearScene.view   model
    NewMember       -> NewMemberScene.view       model
    NewUser         -> NewUserScene.view         model
    OldBusiness     -> OldBusinessScene.view     model
    PublicHours     -> PublicHoursScene.view     model
    ReasonForVisit  -> ReasonForVisitScene.view  model
    RfidHelper      -> RfidHelper.view           model
    SignUpDone      -> SignUpDoneScene.view      model
    Start           -> StartScene.view           model
    TaskInfo        -> TaskInfoScene.view        model
    TaskList        -> TaskListScene.view        model
    TimeSheetPt1    -> TimeSheetPt1Scene.view    model
    TimeSheetPt2    -> TimeSheetPt2Scene.view    model
    TimeSheetPt3    -> TimeSheetPt3Scene.view    model
    UseBankedHours  -> UseBankedHoursScene.view  model
    Waiver          -> WaiverScene.view          model
    WelcomeForRfid  -> WelcomeForRfidScene.view  model
    Welcome         -> WelcomeScene.view         model
    YouCantEnter    -> YouCantEnterScene.view    model


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------

subscriptions: Model -> Sub Msg
subscriptions model =
  let
    focusSetSubs = focusWasSet (WizardVector << FocusWasSet)
    rfidHelperSubs = RfidHelper.subscriptions
    startSubs = StartScene.subscriptions model
    timeTickSubs = Time.every second (WizardVector << Tick)
    waiverSubs = WaiverScene.subscriptions model
  in
    Sub.batch
      [ focusSetSubs
      , rfidHelperSubs
      , startSubs
      , timeTickSubs
      , waiverSubs
      ]


-----------------------------------------------------------------------------
-- UTILITIES
-----------------------------------------------------------------------------

send : msg -> Cmd msg
send msg =
  Task.succeed msg
  |> Task.perform identity
