port module ReceptionKiosk exposing (..)

-- Standard
import Html exposing (Html, Attribute, a, div, text, span, button, br, p, img, h1, h2, ol, li, b, canvas)
import Html.Attributes exposing (style, src, id, tabindex, width, height)
import Regex exposing (regex)
import Http
import Time exposing (Time, second)

-- Third party
import List.Nonempty as Nonempty exposing (Nonempty)
import Material

-- Local
import Types exposing (..)
import CheckInScene
import CheckInDoneScene
import CheckOutScene
import CheckOutDoneScene
import CreatingAcctScene
import EmailInUseScene
import HowDidYouHearScene
import MembersOnlyScene
import NewMemberScene
import NewUserScene
import OldBusinessScene
import ReasonForVisitScene
import ScreenSaverScene
import SignUpDoneScene
import TaskListScene
import TimeSheetPt1Scene
import TimeSheetPt2Scene
import TimeSheetPt3Scene
import VolunteerInDoneScene
import WaiverScene
import WelcomeScene
import XisRestApi as XisApi


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
  , sceneStack : Nonempty Scene -- 1st element is the top of the stack
  , doneWithFocus : Bool  -- Only want to set default focus once (per scene transition)
  , idxToFocus : Maybe (List Int)  -- Can't use Material.Component.Index (https://github.com/debois/elm-mdl/issues/342)
  -- elm-mdl model:
  , mdl : Material.Model
  -- api models:
  , xisSession : XisApi.Session Msg
  -- Scene models:
  , checkInModel         : CheckInScene.CheckInModel
  , checkInDoneModel     : CheckInDoneScene.CheckInDoneModel
  , checkOutModel        : CheckOutScene.CheckOutModel
  , checkOutDoneModel    : CheckOutDoneScene.CheckOutDoneModel
  , creatingAcctModel    : CreatingAcctScene.CreatingAcctModel
  , emailInUseModel      : EmailInUseScene.EmailInUseModel
  , howDidYouHearModel   : HowDidYouHearScene.HowDidYouHearModel
  , membersOnlyModel     : MembersOnlyScene.MembersOnlyModel
  , screenSaverModel     : ScreenSaverScene.ScreenSaverModel
  , signUpDoneModel      : SignUpDoneScene.SignUpDoneModel
  , newMemberModel       : NewMemberScene.NewMemberModel
  , newUserModel         : NewUserScene.NewUserModel
  , oldBusinessModel     : OldBusinessScene.OldBusinessModel
  , reasonForVisitModel  : ReasonForVisitScene.ReasonForVisitModel
  , taskListModel        : TaskListScene.TaskListModel
  , timeSheetPt1Model    : TimeSheetPt1Scene.TimeSheetPt1Model
  , timeSheetPt2Model    : TimeSheetPt2Scene.TimeSheetPt2Model
  , timeSheetPt3Model    : TimeSheetPt3Scene.TimeSheetPt3Model
  , volunteerInDoneModel : VolunteerInDoneScene.VolunteerInDoneModel
  , waiverModel          : WaiverScene.WaiverModel
  , welcomeModel         : WelcomeScene.WelcomeModel
  }

init : Flags -> (Model, Cmd Msg)
init f =
  let
    (checkInModel,         checkInCmd        ) = CheckInScene.init         f
    (checkInDoneModel,     checkInDoneCmd    ) = CheckInDoneScene.init     f
    (checkOutModel,        checkOutCmd       ) = CheckOutScene.init        f
    (checkOutDoneModel,    checkOutDoneCmd   ) = CheckOutDoneScene.init    f
    (creatingAcctModel,    creatingAcctCmd   ) = CreatingAcctScene.init    f
    (emailInUseModel,      emailInUseCmd     ) = EmailInUseScene.init      f
    (howDidYouHearModel,   howDidYouHearCmd  ) = HowDidYouHearScene.init   f
    (membersOnlyModel,     membersOnlyCmd    ) = MembersOnlyScene.init     f
    (newMemberModel,       newMemberCmd      ) = NewMemberScene.init       f
    (newUserModel,         newUserCmd        ) = NewUserScene.init         f
    (oldBusinessModel,     oldBusinessCmd    ) = OldBusinessScene.init     f
    (reasonForVisitModel,  reasonForVisitCmd ) = ReasonForVisitScene.init  f
    (screenSaverModel,     screenSaverCmd    ) = ScreenSaverScene.init     f
    (signUpDoneModel,      signUpDoneCmd     ) = SignUpDoneScene.init      f
    (taskListModel,        taskListCmd       ) = TaskListScene.init        f
    (timeSheetPt1Model,    timeSheetPt1Cmd   ) = TimeSheetPt1Scene.init    f
    (timeSheetPt2Model,    timeSheetPt2Cmd   ) = TimeSheetPt2Scene.init    f
    (timeSheetPt3Model,    timeSheetPt3Cmd   ) = TimeSheetPt3Scene.init    f
    (volunteerInDoneModel, volunteerInDoneCmd) = VolunteerInDoneScene.init f
    (waiverModel,          waiverCmd         ) = WaiverScene.init          f
    (welcomeModel,         welcomeCmd        ) = WelcomeScene.init         f
    model =
      { flags = f
      , currTime = 0
      , sceneStack = Nonempty.fromElement ScreenSaver
      , doneWithFocus = False
      , idxToFocus = Nothing
      , mdl = Material.model
      , xisSession = XisApi.createSession f
      -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
      , checkInModel         = checkInModel
      , checkInDoneModel     = checkInDoneModel
      , checkOutModel        = checkOutModel
      , checkOutDoneModel    = checkOutDoneModel
      , creatingAcctModel    = creatingAcctModel
      , emailInUseModel      = emailInUseModel
      , howDidYouHearModel   = howDidYouHearModel
      , membersOnlyModel     = membersOnlyModel
      , newMemberModel       = newMemberModel
      , newUserModel         = newUserModel
      , oldBusinessModel     = oldBusinessModel
      , reasonForVisitModel  = reasonForVisitModel
      , screenSaverModel     = screenSaverModel
      , signUpDoneModel      = signUpDoneModel
      , taskListModel        = taskListModel
      , timeSheetPt1Model    = timeSheetPt1Model
      , timeSheetPt2Model    = timeSheetPt2Model
      , timeSheetPt3Model    = timeSheetPt3Model
      , volunteerInDoneModel = volunteerInDoneModel
      , waiverModel          = waiverModel
      , welcomeModel         = welcomeModel
      }
    cmds =
      [ checkInCmd
      , checkInDoneCmd
      , checkOutCmd
      , checkOutDoneCmd
      , creatingAcctCmd
      , emailInUseCmd
      , howDidYouHearCmd
      , membersOnlyCmd
      , newMemberCmd
      , newUserCmd
      , reasonForVisitCmd
      , screenSaverCmd
      , taskListCmd
      , timeSheetPt1Cmd
      , timeSheetPt2Cmd
      , timeSheetPt3Cmd
      , volunteerInDoneCmd
      , waiverCmd
      , welcomeCmd
      ]
  in
    (model, Cmd.batch cmds)


setIndexToFocus : Maybe (List Int) -> Model -> Model
setIndexToFocus index model =
  {model | idxToFocus = index}


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

        Rebase ->
          -- Resets the stack so that top item becomes ONLY item. Prevents BACK.
          let
            newModel = {model | sceneStack = Nonempty.dropTail model.sceneStack }
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

        Reset -> reset model

        SceneWillAppear appearing vanishing ->
          -- REVIEW: Standardize so that every scene gets both appearing and vanishing?
          let
            -- REVIEW: It's too easy to forget to add these.
            (mCI,  cCI)  = CheckInScene.sceneWillAppear model appearing
            (mCO,  cCO)  = CheckOutScene.sceneWillAppear model appearing
            (mCA,  cCA)  = CreatingAcctScene.sceneWillAppear model appearing
            (mHD,  cHD)  = HowDidYouHearScene.sceneWillAppear model appearing
            (mMO,  cMO)  = MembersOnlyScene.sceneWillAppear model appearing
            (mNM,  cNM)  = NewMemberScene.sceneWillAppear model appearing
            (mNU,  cNU)  = NewUserScene.sceneWillAppear model appearing
            (mOB,  cOB)  = OldBusinessScene.sceneWillAppear model appearing vanishing
            (mSS,  cSS)  = ScreenSaverScene.sceneWillAppear model appearing
            (mSUD, cSUD) = SignUpDoneScene.sceneWillAppear model appearing vanishing
            (mTL,  cTL)  = TaskListScene.sceneWillAppear model appearing vanishing
            (mTS1, cTS1) = TimeSheetPt1Scene.sceneWillAppear model appearing vanishing
            (mTS2, cTS2) = TimeSheetPt2Scene.sceneWillAppear model appearing vanishing
            (mTS3, cTS3) = TimeSheetPt3Scene.sceneWillAppear model appearing vanishing
            (mVID, cVID) = VolunteerInDoneScene.sceneWillAppear model appearing vanishing
            (mW,   cW)   = WaiverScene.sceneWillAppear model appearing
            newModel =
              -- REVIEW: It's too easy to forget to add these.
              { model
              | idxToFocus = Nothing
              , doneWithFocus = False
              , checkInModel = mCI
              , checkOutModel = mCO
              , creatingAcctModel = mCA
              , howDidYouHearModel = mHD
              , membersOnlyModel = mMO
              , newMemberModel = mNM
              , newUserModel = mNU
              , oldBusinessModel = mOB
              , screenSaverModel = mSS
              , signUpDoneModel = mSUD
              , taskListModel = mTL
              , timeSheetPt1Model = mTS1
              , timeSheetPt2Model = mTS2
              , timeSheetPt3Model = mTS3
              , volunteerInDoneModel = mVID
              , waiverModel = mW
              }
          in
            (newModel, Cmd.batch
              -- REVIEW: It's too easy to forget to add these.
              [ cCI, cCO, cCA, cHD, cMO, cNM, cNU, cOB
              , cSS, cSUD, cTL, cTS1, cTS2, cTS3, cVID, cW
              ]
            )

        Tick time ->
          let
            (mCA, cCA) = CreatingAcctScene.tick time model
            (mCI, cCI) = CheckInScene.tick time model
            (mSS, cSS) = ScreenSaverScene.tick time model
            newModel =
              { model
              | currTime = time
              , creatingAcctModel = mCA
              , checkInModel = mCI
              , screenSaverModel = mSS
              }
            cmdFocus =
              case (model.doneWithFocus, model.idxToFocus) of
                (False, Just idx) ->
                  idx |> toString |> setFocusIfNoFocus
                _ -> Cmd.none
          in
            (newModel, Cmd.batch [cmdFocus, cCA, cCI, cSS])

        FocusOnIndex idx ->
          let
            -- REVIEW: Why did previous version always also check && List.isEmpty model.badNews
            cmd = if not model.doneWithFocus
              then model.idxToFocus |> toString |> setFocusIfNoFocus
              else Cmd.none
          in
            ({model | idxToFocus=idx, doneWithFocus=False}, cmd)

        FocusWasSet wasSet ->
          if wasSet then
            ({model | doneWithFocus=True, idxToFocus=Nothing}, Cmd.none)
          else
            (model, Cmd.none)

    CheckInVector x ->
      let (sm, cmd) = CheckInScene.update x model
      in ({model | checkInModel = sm}, cmd)

    CheckOutVector x ->
      let (sm, cmd) = CheckOutScene.update x model
      in ({model | checkOutModel = sm}, cmd)

    CreatingAcctVector x ->
      let (sm, cmd) = CreatingAcctScene.update x model
      in ({model | creatingAcctModel = sm}, cmd)

    HowDidYouHearVector x ->
      let (sm, cmd) = HowDidYouHearScene.update x model
      in ({model | howDidYouHearModel = sm}, cmd)

    MembersOnlyVector x ->
      let (sm, cmd) = MembersOnlyScene.update x model
      in ({model | membersOnlyModel = sm}, cmd)

    NewMemberVector x ->
      let (sm, cmd) = NewMemberScene.update x model
      in ({model | newMemberModel = sm}, cmd)

    NewUserVector x ->
      let (sm, cmd) = NewUserScene.update x model
      in ({model | newUserModel = sm}, cmd)

    OldBusinessVector x ->
      let (sm, cmd) = OldBusinessScene.update x model
      in ({model | oldBusinessModel = sm}, cmd)

    ReasonForVisitVector x ->
      let (sm, cmd) = ReasonForVisitScene.update x model
      in ({model | reasonForVisitModel = sm}, cmd)

    ScreenSaverVector x ->
      let (sm, cmd) = ScreenSaverScene.update x model
      in ({model | screenSaverModel = sm}, cmd)

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

    WaiverVector x ->
      let (sm, cmd) = WaiverScene.update x model
      in ({model | waiverModel = sm}, cmd)

    MdlVector x ->
      Material.update MdlVector x model


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : Model -> Html Msg
view model =
  let currScene = Nonempty.head model.sceneStack
  in case currScene of
    CheckIn         -> CheckInScene.view         model
    CheckInDone     -> CheckInDoneScene.view     model
    CheckOut        -> CheckOutScene.view        model
    CheckOutDone    -> CheckOutDoneScene.view    model
    CreatingAcct    -> CreatingAcctScene.view    model
    EmailInUse      -> EmailInUseScene.view      model
    HowDidYouHear   -> HowDidYouHearScene.view   model
    MembersOnly     -> MembersOnlyScene.view     model
    NewMember       -> NewMemberScene.view       model
    NewUser         -> NewUserScene.view         model
    OldBusiness     -> OldBusinessScene.view     model
    ReasonForVisit  -> ReasonForVisitScene.view  model
    ScreenSaver     -> ScreenSaverScene.view     model
    SignUpDone      -> SignUpDoneScene.view      model
    TaskList        -> TaskListScene.view        model
    TimeSheetPt1    -> TimeSheetPt1Scene.view    model
    TimeSheetPt2    -> TimeSheetPt2Scene.view    model
    TimeSheetPt3    -> TimeSheetPt3Scene.view    model
    VolunteerInDone -> VolunteerInDoneScene.view model
    Waiver          -> WaiverScene.view          model
    Welcome         -> WelcomeScene.view         model


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------

subscriptions: Model -> Sub Msg
subscriptions model =
  let
    focusSetSub = focusWasSet (WizardVector << FocusWasSet)
    timeTickSub = Time.every second (WizardVector << Tick)
    screenSaverSubs = ScreenSaverScene.subscriptions model
    waiverSubs = WaiverScene.subscriptions model
  in
    Sub.batch
      [ focusSetSub
      , timeTickSub
      , screenSaverSubs
      , waiverSubs
      ]
