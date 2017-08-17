module ReceptionKiosk exposing (..)

-- Standard
import Html exposing (Html, Attribute, a, div, text, span, button, br, p, img, h1, h2, ol, li, b, canvas)
import Html.Attributes exposing (style, src, id, tabindex, width, height)
import Regex exposing (regex)
import Http

-- Third party
import List.Nonempty exposing (Nonempty)
import Material
import Update.Extra exposing (andThen)
import Update.Extra.Infix exposing ((:>))

-- Local
import ReceptionKiosk.Types exposing (..)
import ReceptionKiosk.CheckInScene as CheckInScene
import ReceptionKiosk.CheckInDoneScene as CheckInDoneScene
import ReceptionKiosk.CheckOutScene as CheckOutScene
import ReceptionKiosk.CheckOutDoneScene as CheckOutDoneScene
import ReceptionKiosk.DoYouHaveAcctScene as DoYouHaveAcctScene
import ReceptionKiosk.HowDidYouHearScene as HowDidYouHearScene
import ReceptionKiosk.NewMemberScene as NewMemberScene
import ReceptionKiosk.NewUserScene as NewUserScene
import ReceptionKiosk.ReasonForVisitScene as ReasonForVisitScene
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
  , mdl : Material.Model  -- TODO: Should there be one dedicated Material model per scene so index scope is smaller?
  -- Scene models:
  , checkInModel        : CheckInScene.CheckInModel
  , checkInDoneModel    : CheckInDoneScene.CheckInDoneModel
  , checkOutModel       : CheckOutScene.CheckOutModel
  , checkOutDoneModel   : CheckOutDoneScene.CheckOutDoneModel
  , doYouHaveAcctModel  : DoYouHaveAcctScene.DoYouHaveAcctModel
  , howDidYouHearModel  : HowDidYouHearScene.HowDidYouHearModel
  , newMemberModel      : NewMemberScene.NewMemberModel
  , newUserModel        : NewUserScene.NewUserModel
  , reasonForVisitModel : ReasonForVisitScene.ReasonForVisitModel
  , waiverModel         : WaiverScene.WaiverModel
  , welcomeModel        : WelcomeScene.WelcomeModel
  }

init : Flags -> (Model, Cmd Msg)
init f =
  let
    (checkInModel,        checkInCmd       ) = CheckInScene.init        f
    (checkInDoneModel,    checkInDoneCmd   ) = CheckInDoneScene.init    f
    (checkOutModel,       checkOutCmd      ) = CheckOutScene.init       f
    (checkOutDoneModel,   checkOutDoneCmd  ) = CheckOutDoneScene.init   f
    (doYouHaveAcctModel,  doYouHaveAcctCmd ) = DoYouHaveAcctScene.init  f
    (howDidYouHearModel,  howDidYouHearCmd ) = HowDidYouHearScene.init  f
    (newMemberModel,      newMemberCmd     ) = NewMemberScene.init      f
    (newUserModel,        newUserCmd       ) = NewUserScene.init        f
    (reasonForVisitModel, reasonForVisitCmd) = ReasonForVisitScene.init f
    (waiverModel,         waiverCmd        ) = WaiverScene.init         f
    (welcomeModel,        welcomeCmd       ) = WelcomeScene.init        f
    model =
      { flags = f
      , sceneStack = List.Nonempty.fromElement Welcome
      , mdl = Material.model
      -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
      , checkInModel        = checkInModel
      , checkInDoneModel    = checkInDoneModel
      , checkOutModel       = checkOutModel
      , checkOutDoneModel   = checkOutDoneModel
      , doYouHaveAcctModel  = doYouHaveAcctModel
      , howDidYouHearModel  = howDidYouHearModel
      , newMemberModel      = newMemberModel
      , newUserModel        = newUserModel
      , reasonForVisitModel = reasonForVisitModel
      , waiverModel         = waiverModel
      , welcomeModel        = welcomeModel
      }
    cmds =
      [ checkInCmd
      , checkInDoneCmd
      , checkOutCmd
      , checkOutDoneCmd
      , doYouHaveAcctCmd
      , howDidYouHearCmd
      , newMemberCmd
      , newUserCmd
      , reasonForVisitCmd
      , waiverCmd
      , welcomeCmd
      ]
  in
    (model, Cmd.batch cmds)

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

    Push nextScene ->
      -- Push the new scene onto the scene stack.
      let
        newModel = {model | sceneStack = List.Nonempty.cons nextScene model.sceneStack }
      in
        (newModel, Cmd.none) :> update (SceneWillAppear nextScene)

    Pop ->
      -- Pop the top scene off the stack.
      let
        newModel = {model | sceneStack = List.Nonempty.pop model.sceneStack }
        newScene = List.Nonempty.head newModel.sceneStack
      in
        (newModel, Cmd.none) :> update (SceneWillAppear newScene)

    Reset -> reset model

    SceneWillAppear appearingScene ->
        case appearingScene of
          CheckOut -> (model, Cmd.none) :> update (CheckOutVector CheckOutSceneWillAppear)
          Waiver -> (model, Cmd.none) :> update (WaiverVector WaiverSceneWillAppear)
          Welcome -> (model, Cmd.none) :> update (WelcomeVector WelcomeSceneWillAppear)
          _ -> (model, Cmd.none)

    CheckInVector x ->
      let (sm, cmd) = CheckInScene.update x model
      in ({model | checkInModel = sm}, cmd)

    CheckOutVector x ->
      let (sm, cmd) = CheckOutScene.update x model
      in ({model | checkOutModel = sm}, cmd)

    HowDidYouHearVector x ->
      let (sm, cmd) = HowDidYouHearScene.update x model
      in ({model | howDidYouHearModel = sm}, cmd)

    NewMemberVector x ->
      let (sm, cmd) = NewMemberScene.update x model
      in ({model | newMemberModel = sm}, cmd)

    NewUserVector x ->
      let (sm, cmd) = NewUserScene.update x model
      in ({model | newUserModel = sm}, cmd)

    ReasonForVisitVector x ->
      let (sm, cmd) = ReasonForVisitScene.update x model
      in ({model | reasonForVisitModel = sm}, cmd)

    WaiverVector x ->
      let (sm, cmd) = WaiverScene.update x model
      in ({model | waiverModel = sm}, cmd)

    WelcomeVector x ->
      let (sm, cmd) = WelcomeScene.update x model
      in ({model | welcomeModel = sm}, cmd)

    MdlVector x ->
      Material.update MdlVector x model

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : Model -> Html Msg
view model =
  let currScene = List.Nonempty.head model.sceneStack
  in case currScene of
    CheckIn        -> CheckInScene.view        model
    CheckInDone    -> CheckInDoneScene.view    model
    CheckOut       -> CheckOutScene.view       model
    CheckOutDone   -> CheckOutDoneScene.view   model
    DoYouHaveAcct  -> DoYouHaveAcctScene.view  model
    HowDidYouHear  -> HowDidYouHearScene.view  model
    NewMember      -> NewMemberScene.view      model
    NewUser        -> NewUserScene.view        model
    ReasonForVisit -> ReasonForVisitScene.view model
    Waiver         -> WaiverScene.view         model
    Welcome        -> WelcomeScene.view        model

-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------

subscriptions: Model -> Sub Msg
subscriptions model =
  let
    waiverSubs = WaiverScene.subscriptions model
    subs = [waiverSubs]
  in
    Sub.batch subs


