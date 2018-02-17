
module ScreenSaverScene exposing
  ( init
  , rfidWasSwiped
  , sceneWillAppear
  , tick
  , update
  , view
  , subscriptions
  -------------------
  , ScreenSaverModel
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
import XisRestApi as XisApi exposing (..)


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
  , screenSaverModel : ScreenSaverModel
  }


type alias ScreenSaverModel =
  { idleSeconds : Int
  , badNews : List String
  }


init : Flags -> (ScreenSaverModel, Cmd Msg)
init flags =
  ( { idleSeconds = 0
    , badNews = []
    }
    ,
    Cmd.none
  )


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (ScreenSaverModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  let
    sceneModel = kioskModel.screenSaverModel
  in
    if appearingScene == ScreenSaver then
      ({sceneModel | idleSeconds=0}, hideKeyboard ())
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

    SS_MouseClick ->
      if amVisible && sceneModel.idleSeconds > 0 then
        -- Note: idleSeconds == 0 means the click was on the scene that segued to here.
        (sceneModel, segueTo Welcome)
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
    CheckIn -> 60
    CheckInDone -> 5
    CheckOut -> 60
    CheckOutDone -> 5
    CreatingAcct -> 300
    EmailInUse -> 300
    HowDidYouHear -> 300
    MembersOnly -> 300
    NewMember -> 600
    NewUser -> 600
    OldBusiness -> 300
    ReasonForVisit -> 300
    ScreenSaver -> 86400
    SignUpDone -> 300
    TaskList -> 300
    TimeSheetPt1 -> 300
    TimeSheetPt2 -> 600  -- Give them time to type a description, get distracted, and continue.
    TimeSheetPt3 -> 600  -- Give them some time to find a staffer.
    TaskInfo -> 600  -- There may be a lot to read in the instructions.
    Waiver -> 600
    Welcome -> 60
    WelcomeForRfid -> 60


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
    [ Mouse.clicks (\_ -> (ScreenSaverVector <| SS_MouseClick))
    , Keyboard.downs (ScreenSaverVector << SS_KeyDown)
    ]


-----------------------------------------------------------------------------
-- RFID WAS SWIPED
-----------------------------------------------------------------------------

rfidWasSwiped : KioskModel a -> Result String Member -> (ScreenSaverModel, Cmd Msg)
rfidWasSwiped kioskModel result =
  case result of
    Ok m -> (kioskModel.screenSaverModel, segueTo WelcomeForRfid)
    Err e -> (kioskModel.screenSaverModel, Cmd.none)



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