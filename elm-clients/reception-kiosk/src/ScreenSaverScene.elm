
module ScreenSaverScene exposing
  ( init
  , sceneWillAppear
  , update
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
msgDivHeight = 419  -- Measured in browser
xPos = (sceneWidth - msgDivWidth) // 2
yPos = -100 + (sceneHeight - msgDivHeight) // 2


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias ScreenSaverModel =
  { charsTyped : List Char
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a = SceneUtilModel
  { a
  | screenSaverModel : ScreenSaverModel
  }

init : Flags -> (ScreenSaverModel, Cmd Msg)
init flags =
  ({charsTyped=[]}, Cmd.none)


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (ScreenSaverModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  let
    sceneModel = kioskModel.screenSaverModel
  in
    if appearingScene == Welcome
      then
        ({sceneModel | charsTyped = []}, hideKeyboard ())
      else
        (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : ScreenSaverMsg -> KioskModel a -> (ScreenSaverModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.screenSaverModel
  in case msg of

    UserActivityNoted ->
      (sceneModel, segueTo Welcome)

    WakeOrRfidKeyStroke code ->
      let
        newChar = Char.fromCode code
        prevChars = sceneModel.charsTyped
        isWake = newChar == ' '
      in
        if isWake then
          update UserActivityNoted kioskModel
        else
          ({sceneModel | charsTyped = newChar :: prevChars }, Cmd.none)


-----------------------------------------------------------------------------
-- TICK (called each second)
-----------------------------------------------------------------------------


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
        [ img [src "/static/bzw_ops/Logo, Light, 100w.png", logoImgStyle] []
        , vspace 35
        , h1 [h1Style] [text "Welcome!"]
        , vspace 0
        , h1 [h1Style] [text "All Visitors Must Sign In"]
        , vspace 30
        , h2 [h2Style] [text "Tap Spacebar to Start"]
        ]
      ]


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------

subscriptions: KioskModel a -> Sub Msg
subscriptions model =
  if sceneIsVisible model ScreenSaver
    then
      Sub.batch
        [ Mouse.clicks (\_ -> (ScreenSaverVector <| UserActivityNoted))
        , Keyboard.downs (ScreenSaverVector << WakeOrRfidKeyStroke)
        ]
    else
      Sub.none


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
  , "color" => "red"
  , "position" => "relative"
  , "display" => "inline-block"
  ]

logoImgStyle = style
  [ "width" => px 200
  ]

h1Style = style
  [ "font-family" => "roboto condensed"
  , "font-size" => "54pt"
  , "word-spacing" => "-5px"
  , "line-height" => "0.9"
  , "margin" => "0"
  ]

h2Style = style
  [ "line-height" => "1"
  , "margin" => "0"
  , "font-size" => "24pt"
  , "color" => "white"
  ]