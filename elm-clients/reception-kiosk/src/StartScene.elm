
module StartScene exposing
  ( init
  , rfidWasSwiped
  , sceneWillAppear
  , tick
  , update
  , view
  , subscriptions
  -------------------
  , StartModel
  )

-- Standard
import Html exposing (Html, div, text, img, br, h1, h2, audio)
import Html.Attributes exposing (src, width, style, autoplay)
import Time exposing (Time)
import Mouse
import Keyboard
import Char


-- Third Party
import Material
import List.Nonempty exposing (Nonempty)

-- Local
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import XisRestApi as XisApi


-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------


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
  , startModel : StartModel
  , xisSession : XisApi.Session Msg
  }


type alias StartModel =
  { idleSeconds : Int
  }


init : Flags -> (StartModel, Cmd Msg)
init flags =
  ( { idleSeconds = 0
    }
    ,
    Cmd.none
  )


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (StartModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  let
    sceneModel = kioskModel.startModel
  in
    if appearingScene == Start then
      ({sceneModel | idleSeconds=0}, hideKeyboard ())
    else
      ({sceneModel | idleSeconds=0}, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : StartMsg -> KioskModel a -> (StartModel, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.startModel
    amVisible = currentScene kioskModel == Start

  in
    case msg of

    SS_MouseClick pos ->
      if amVisible && sceneModel.idleSeconds > 0 then
        -- Note: idleSeconds == 0 means the click was on the scene that segued to here.
        let
          segueCmd = segueTo Welcome
          msgToLog = "Start Scene clicked at: "++(toString pos)
          logCmd =
            kioskModel.xisSession.logMessage
              "kiosk" -- The logger to be used on the servers side
              XisApi.LL_Info  -- The logging level
              msgToLog
              IgnoreResultHttpErrorString  -- A no-op handler for Result Http.Error String
        in
          (sceneModel, Cmd.batch [segueCmd, logCmd])
      else
        -- It's a mouse click on some other scene, so reset idle time.
        ({sceneModel | idleSeconds=0}, Cmd.none)

    SS_KeyDown code ->
      if amVisible then
        case code of  -- REVIEW: Maybe allow any keystroke?
          32 ->
            -- Spacebar
            (sceneModel, segueTo Welcome)
          _ ->
            -- Uninteresting code
            (sceneModel, Cmd.none)
      else
        -- It's a key down on some other scene, so reset idle time.
        ({sceneModel | idleSeconds=0}, Cmd.none)


-----------------------------------------------------------------------------
-- TICK (called each second)
-----------------------------------------------------------------------------

timeoutFor : Scene -> Int
timeoutFor scene =
  case scene of
    AuthorizeEntry -> 300  -- But this scene never appears.
    BuyMembership -> 300
    CheckIn -> 60
    CheckInDone -> 5
    CheckOut -> 60
    CheckOutDone -> 5
    CreatingAcct -> 300
    EmailInUse -> 300
    Error -> 600
    HowDidYouHear -> 300
    NewMember -> 600
    NewUser -> 600
    OldBusiness -> 300
    PublicHours -> 300
    ReasonForVisit -> 300
    RfidHelper -> 600
    SignUpDone -> 300
    Start -> 86400
    TaskList -> 300
    TimeSheetPt1 -> 300
    TimeSheetPt2 -> 600  -- Give them time to type a description, get distracted, and continue.
    TimeSheetPt3 -> 600  -- Give them some time to find a staffer.
    TaskInfo -> 600  -- There may be a lot to read in the instructions.
    UseBankedHours -> 300
    Waiver -> 600
    Welcome -> 60
    WelcomeForRfid -> 30
    YouCantEnter -> 300

tick : Time -> KioskModel a -> (StartModel, Cmd Msg)
tick time kioskModel =
  let
    sceneModel = kioskModel.startModel
    newSeconds = sceneModel.idleSeconds + 1
    newSceneModel = {sceneModel | idleSeconds = newSeconds}
    tooLong = timeoutFor (currentScene kioskModel)
    cmd = if newSeconds > tooLong then send (WizardVector <| Reset) else Cmd.none
  in
    (newSceneModel, cmd)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  genericScene kioskModel
    ""
    ""
    (div []
      [ vspace 20
      -- REVIEW: Do I want to pass all imgs in as flags, as was done with banners?
      , img [src kioskModel.flags.wavingHandUrl, logoImgStyle] []
      , vspace 20
      , h1 [h1Style] [text "Welcome!"]
      , vspace 0
      , h1 [h1Style] [text "All Visitors Must Sign In"]
      , vspace 30
      , h2 [h2Style] [text "Tap Spacebar or Screen to Start"]
      ]
    )
    []
    []


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------

subscriptions: KioskModel a -> Sub Msg
subscriptions model =
  Sub.batch
    [ Mouse.clicks (StartVector << SS_MouseClick)
    , Keyboard.downs (StartVector << SS_KeyDown)
    ]


-----------------------------------------------------------------------------
-- RFID WAS SWIPED
-----------------------------------------------------------------------------

rfidWasSwiped : KioskModel a -> Result String XisApi.Member -> (StartModel, Cmd Msg)
rfidWasSwiped kioskModel result =
  case result of
    Ok m -> (kioskModel.startModel, send <| WelcomeForRfidVector <| W4R_Segue m)
    Err e -> (kioskModel.startModel, Cmd.none)


-----------------------------------------------------------------------------
-- STYLE
-----------------------------------------------------------------------------

bgDivStyle = style
  [ "background-color" => "black"
  , "height" => px sceneHeight
  , "width" => px sceneWidth
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "text-align" => "center"
  , "font-size" => "36pt"
  ]

logoImgStyle = style
  [ "width" => px 600
  , "height" => px 579
  ]

h1Style = style
  [ "font-family" => "roboto condensed"
  , "font-size" => "54pt"
  , "word-spacing" => "-5px"
  , "line-height" => "0.9"
  , "margin" => "0"
  , "color" => "black"
  ]

h2Style = style
  [ "line-height" => "1"
  , "margin" => "0"
  , "font-size" => "24pt"
  , "color" => "black"
  ]