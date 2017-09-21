module ReceptionKiosk exposing (..)

-- Standard
import Html exposing (Html, Attribute, a, div, text, span, button, br, p, img, h1, h2, ol, li, b, canvas)
import Html.Attributes exposing (style, src, id, tabindex, width, height)
import Regex exposing (regex)
import Http
import Time exposing (Time, second)

-- Third party
import List.Nonempty exposing (Nonempty)
import Material
import Update.Extra.Infix exposing ((:>))

-- Local
import ReceptionKiosk.Types exposing (..)
import ReceptionKiosk.CheckInScene as CheckInScene
import ReceptionKiosk.CheckInDoneScene as CheckInDoneScene
import ReceptionKiosk.CheckOutScene as CheckOutScene
import ReceptionKiosk.CheckOutDoneScene as CheckOutDoneScene
import ReceptionKiosk.CreatingAcctScene as CreatingAcctScene
import ReceptionKiosk.EmailInUseScene as EmailInUseScene
import ReceptionKiosk.HowDidYouHearScene as HowDidYouHearScene
import ReceptionKiosk.SignUpDoneScene as SignUpDoneScene
import ReceptionKiosk.MembersOnlyScene as MembersOnlyScene
import ReceptionKiosk.NewMemberScene as NewMemberScene
import ReceptionKiosk.NewUserScene as NewUserScene
import ReceptionKiosk.ReasonForVisitScene as ReasonForVisitScene
import ReceptionKiosk.TaskListScene as TaskListScene
import ReceptionKiosk.VolunteerInDoneScene as VolunteerInDoneScene
import ReceptionKiosk.WaiverScene as WaiverScene
import ReceptionKiosk.WelcomeScene as WelcomeScene

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
-- MODEL
-----------------------------------------------------------------------------

type alias Model =
  { flags : Flags
  , sceneStack : Nonempty Scene -- 1st element is the top of the stack
  -- elm-mdl model:
  , mdl : Material.Model
  -- Scene models:
  , checkInModel         : CheckInScene.CheckInModel
  , checkInDoneModel     : CheckInDoneScene.CheckInDoneModel
  , checkOutModel        : CheckOutScene.CheckOutModel
  , checkOutDoneModel    : CheckOutDoneScene.CheckOutDoneModel
  , creatingAcctModel    : CreatingAcctScene.CreatingAcctModel
  , emailInUseModel      : EmailInUseScene.EmailInUseModel
  , howDidYouHearModel   : HowDidYouHearScene.HowDidYouHearModel
  , membersOnlyModel     : MembersOnlyScene.MembersOnlyModel
  , signUpDoneModel      : SignUpDoneScene.SignUpDoneModel
  , newMemberModel       : NewMemberScene.NewMemberModel
  , newUserModel         : NewUserScene.NewUserModel
  , reasonForVisitModel  : ReasonForVisitScene.ReasonForVisitModel
  , taskListModel        : TaskListScene.TaskListModel
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
    (reasonForVisitModel,  reasonForVisitCmd ) = ReasonForVisitScene.init  f
    (signUpDoneModel,      signUpDoneCmd     ) = SignUpDoneScene.init      f
    (taskListModel,        taskListCmd       ) = TaskListScene.init        f
    (volunteerInDoneModel, volunteerInDoneCmd) = VolunteerInDoneScene.init f
    (waiverModel,          waiverCmd         ) = WaiverScene.init          f
    (welcomeModel,         welcomeCmd        ) = WelcomeScene.init         f
    model =
      { flags = f
      , sceneStack = List.Nonempty.fromElement Welcome
      , mdl = Material.model
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
      , reasonForVisitModel  = reasonForVisitModel
      , signUpDoneModel      = signUpDoneModel
      , taskListModel        = taskListModel
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
      , taskListCmd
      , volunteerInDoneCmd
      , waiverCmd
      , welcomeCmd
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

    WizardVector wizMsg ->
      case wizMsg of
        Push nextScene ->
          -- Push the new scene onto the scene stack.
          let
            newModel = {model | sceneStack = List.Nonempty.cons nextScene model.sceneStack }
          in
            (newModel, Cmd.none) :> update (WizardVector <| SceneWillAppear <| nextScene)

        Pop ->
          -- Pop the top scene off the stack.
          let
            newModel = {model | sceneStack = List.Nonempty.pop model.sceneStack }
            newScene = List.Nonempty.head newModel.sceneStack
          in
            (newModel, Cmd.none) :> update (WizardVector <| SceneWillAppear <| newScene)

        RebaseTo newBaseScene ->
          -- Resets the stack with a new base scene.
          let
            newModel = {model | sceneStack = List.Nonempty.fromElement newBaseScene }
          in
            (newModel, Cmd.none) :> update (WizardVector <| SceneWillAppear <| newBaseScene)

        Reset -> reset model

        SceneWillAppear appearingScene ->

          let
            (m1, c1) = CheckOutScene.sceneWillAppear model appearingScene
            (m2, c2) = CreatingAcctScene.sceneWillAppear model appearingScene
            (m3, c3) = MembersOnlyScene.sceneWillAppear model appearingScene
            (m4, c4) = TaskListScene.sceneWillAppear model appearingScene
            (m5, c5) = WaiverScene.sceneWillAppear model appearingScene
            (m6, c6) = WelcomeScene.sceneWillAppear model appearingScene
            newModel =
              { model
              | checkOutModel = m1
              , creatingAcctModel = m2
              , membersOnlyModel = m3
              , taskListModel = m4
              , waiverModel = m5
              , welcomeModel = m6
              }
          in
            (newModel, Cmd.batch [c1, c2, c3, c4, c5, c6])

        Tick time ->
          let currScene = List.Nonempty.head model.sceneStack
          in case currScene of

            CreatingAcct ->
              let (sm, cmd) = CreatingAcctScene.tick time model
              in ({model | creatingAcctModel = sm}, cmd)

            CheckInDone ->
              let (sm, cmd) = CheckInDoneScene.tick time model
              in ({model | checkInDoneModel = sm}, cmd)

            _ -> (model, Cmd.none)

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

    ReasonForVisitVector x ->
      let (sm, cmd) = ReasonForVisitScene.update x model
      in ({model | reasonForVisitModel = sm}, cmd)

    TaskListVector x ->
      let (sm, cmd) = TaskListScene.update x model
      in ({model | taskListModel = sm}, cmd)

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
  let currScene = List.Nonempty.head model.sceneStack
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
    ReasonForVisit  -> ReasonForVisitScene.view  model
    SignUpDone      -> SignUpDoneScene.view      model
    TaskList        -> TaskListScene.view        model
    VolunteerInDone -> VolunteerInDoneScene.view model
    Waiver          -> WaiverScene.view          model
    Welcome         -> WelcomeScene.view         model

-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------

subscriptions: Model -> Sub Msg
subscriptions model =
  let
    mySubs = Time.every second (WizardVector << Tick)
    waiverSubs = WaiverScene.subscriptions model
    subs = [mySubs, waiverSubs]
  in
    Sub.batch subs
