
module ScreenSaverScene exposing
  ( init
  , sceneWillAppear
  , update
  , tick
  , view
  , subscriptions
  , ScreenSaverModel
  )

-- Standard
import Html exposing (Html, div, text, img, br, h1, h2)
import Html.Attributes exposing (src, width, style)
import Time exposing (Time)
import Random
import Mouse
import Keyboard
import Char


-- Third Party

-- Local
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import Fetchable exposing (..)

-- ScreenSaver piggybacks on the time block checking of MembersOnly.
-- REVIEW: Maybe the time block tracking functionality should be moved somewhere neutral.
import MembersOnlyScene exposing (MembersOnlyModel)


-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------

msgDivWidth = 619  -- Measured in browser
msgDivHeight = 612  -- Measured in browser
xPos = (sceneWidth - msgDivWidth) // 2
yPos = -50 + (sceneHeight - msgDivHeight) // 2

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias ScreenSaverModel =
  { charsTyped : List Char
  , idleSeconds : Int
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a = SceneUtilModel
  { a
  | screenSaverModel : ScreenSaverModel
  }

init : Flags -> (ScreenSaverModel, Cmd Msg)
init flags =
  ({idleSeconds=0, charsTyped=[]}, Cmd.none)


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (ScreenSaverModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  let
    sceneModel = kioskModel.screenSaverModel
  in
    if appearingScene == ScreenSaver then
      ({sceneModel | charsTyped = []}, hideKeyboard ())
    else
      ({sceneModel | idleSeconds=0}, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : ScreenSaverMsg -> KioskModel a -> (ScreenSaverModel, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.screenSaverModel
    amVisible = currentScene kioskModel == ScreenSaver

  in
    case msg of

    ScreenSaverMouseClick ->
      if amVisible && sceneModel.idleSeconds > 0 then
        -- Note: idleSeconds == 0 means the click was on the scene that segued to here.
        (sceneModel, segueTo Welcome)
      else
        -- It's a mouse click on some other scene, so reset idle time.
        ({sceneModel | idleSeconds=0}, Cmd.none)

    ScreenSaverKeyDown code ->
      let
        newChar = Char.fromCode code
        prevChars = sceneModel.charsTyped
        isWakeChar = newChar == ' '
      in
        if amVisible then
          if isWakeChar then
            (sceneModel, segueTo Welcome)
          else
            -- It's presumably an RFID character.
            ({sceneModel | charsTyped = newChar :: prevChars }, Cmd.none)
        else
          -- It's a key down on some other scene, so reset idle time.
          ({sceneModel | idleSeconds=0}, Cmd.none)


-----------------------------------------------------------------------------
-- TICK (called each second)
-----------------------------------------------------------------------------

timeoutFor : Scene -> Int
timeoutFor scene =
  case scene of
    CheckIn -> 60
    CheckInDone -> 10
    CheckOut -> 60
    CheckOutDone -> 10
    CreatingAcct -> 300
    EmailInUse -> 300
    HowDidYouHear -> 300
    MembersOnly -> 300
    NewMember -> 600
    NewUser -> 600
    ReasonForVisit -> 300
    ScreenSaver -> 86400
    SignUpDone -> 300
    TaskList -> 300
    VolunteerInDone -> 300  -- There may be a lot to read in the instructions.
    Waiver -> 600
    Welcome -> 60


tick : Time -> KioskModel a -> (ScreenSaverModel, Cmd Msg)
tick time kioskModel =
  let
    sceneModel = kioskModel.screenSaverModel
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
  let
    sceneModel = kioskModel.screenSaverModel
    positionStyle = style ["top" => px yPos, "left" => px xPos ]
  in
    div [bgDivStyle]
      [ div [msgDivStyle, positionStyle]
        -- TODO: Do I want to pass all imgs in as flags, as was done with banners?
        [ img [src "/static/bzw_ops/SpikeySphere.gif", logoImgStyle] []
        , vspace 20
        , h1 [h1Style, style ["color"=>"white"]] [text "Welcome!"]
        , vspace 0
        , h1 [h1Style, style ["color"=>"red"]] [text "All Visitors Must Sign In"]
        , vspace 30
        , h2 [h2Style] [text "Tap Spacebar or Screen to Start"]
        ]
      ]


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------

subscriptions: KioskModel a -> Sub Msg
subscriptions model =
  Sub.batch
    [ Mouse.clicks (\_ -> (ScreenSaverVector <| ScreenSaverMouseClick))
    , Keyboard.downs (ScreenSaverVector << ScreenSaverKeyDown)
    ]


-----------------------------------------------------------------------------
-- STYLE
-----------------------------------------------------------------------------

bgDivStyle = style
  [ "background-color" => "black"
  , "height" => px sceneHeight
  , "width" => px sceneWidth
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  ]

msgDivStyle = style
  [ "text-align" => "center"
  , "font-size" => "36pt"
  , "position" => "relative"
  , "display" => "inline-block"
  ]

logoImgStyle = style
  [ "width" => px 600
  , "margin" => "-100px"  -- For FiberOptic.gif only.
  ]

h1Style = style
  [ "font-family" => "roboto condensed"
  , "font-size" => "54pt"
  , "word-spacing" => "-5px"
  , "line-height" => "0.9"
  , "margin" => "0"
  , "color" => "#ffff00"
  ]

h2Style = style
  [ "line-height" => "1"
  , "margin" => "0"
  , "font-size" => "24pt"
  , "color" => "white"
  ]