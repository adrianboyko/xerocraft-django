
module ReceptionKiosk.ScreenSaverScene exposing
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

-- Third Party

-- Local
import Wizard.SceneUtils exposing (..)
import ReceptionKiosk.Types exposing (..)


-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------

msgDivWidth = 317  -- Measured in browser
msgDivHeight = 242  -- Measured in browser
redrawPeriod = 3  -- Move msg every redrawPeriod seconds
tooLong = 900  -- Screen saver will activate after tooLong seconds


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias ScreenSaverModel =
  { xPos : Int
  , yPos : Int
  , secondsSinceSceneChange : Int
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a = (SceneUtilModel {a | screenSaverModel : ScreenSaverModel})

init : Flags -> (ScreenSaverModel, Cmd Msg)
init flags =
  let sceneModel =
    { xPos = (sceneWidth - msgDivWidth) // 2
    , yPos = (sceneHeight - msgDivHeight) // 2
    , secondsSinceSceneChange = 0
    }
  in (sceneModel, Cmd.none)

-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (ScreenSaverModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  let
    sceneModel = kioskModel.screenSaverModel
  in
    ({sceneModel | secondsSinceSceneChange = 0}, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : ScreenSaverMsg -> KioskModel a -> (ScreenSaverModel, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.screenSaverModel
  in
    case msg of

      NewMsgPosition (newX, newY) ->
        ({sceneModel | xPos=newX, yPos=newY}, Cmd.none)

      UserActivityNoted ->
        (sceneModel, send (WizardVector <| Pop))


-----------------------------------------------------------------------------
-- TICK (called each second)
-----------------------------------------------------------------------------

tick : Time -> KioskModel a -> (ScreenSaverModel, Cmd Msg)
tick time kioskModel =
  let
    sceneModel = kioskModel.screenSaverModel
    visible = sceneIsVisible kioskModel ScreenSaver
  in
    if visible  -- screen saver IS visible
      then
        if (time |> Time.inSeconds |> floor) % redrawPeriod == 0
          then
            let
              xRandGen = Random.int 0 (sceneWidth - msgDivWidth)
              yRandGen = Random.int 0 (sceneHeight - msgDivHeight)
              pairRandGen = Random.pair xRandGen yRandGen
            in
              (sceneModel, Random.generate (ScreenSaverVector << NewMsgPosition) pairRandGen)
          else
            (sceneModel, Cmd.none)
      else  -- screen saver is NOT visible
        let
          newCount = sceneModel.secondsSinceSceneChange + 1
          cmd = if newCount > tooLong then segueTo ScreenSaver else Cmd.none
        in
          ({sceneModel | secondsSinceSceneChange = newCount}, cmd)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.screenSaverModel
    positionStyle = style ["top" => px sceneModel.yPos, "left" => px sceneModel.xPos ]
  in
    div [bgDivStyle]
      [ div [msgDivStyle, positionStyle]
        -- TODO: Do I want to pass all imgs in as flags, as was done with banners?
        [ img [src "/static/bzw_ops/Logo, Light, 100w.png", logoImgStyle] []
        , h1 [h1Style] [text "Welcome!"]
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
        , Keyboard.presses (\_ -> (ScreenSaverVector <| UserActivityNoted))
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
  [ "width" => px 150
  ]

h1Style = style
  [ "margin" => px 0
  ]

h2Style = style
  [ "margin" => px 0
  , "font-size" => "24pt"
  , "margin-top" => px -10
  , "line-height" => "1"
  ]