
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
import Html exposing (Html, div, text, img, br, h1, h2, audio)
import Html.Attributes exposing (src, width, style, autoplay)
import Time exposing (Time)
import Random
import Mouse
import Keyboard
import Char


-- Third Party

-- Local
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import XisRestApi exposing (..)
import CheckInScene exposing (CheckInModel)

-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type ScreenSaverState
  = Normal
  | CheckingRfid
  | UnknownRfid

type alias ScreenSaverModel =
  { state : ScreenSaverState
  , charsTyped : List Char
  , idleSeconds : Int
  , badNews : List String
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a = SceneUtilModel
  { a
  | screenSaverModel : ScreenSaverModel
  , checkInModel : CheckInModel
  }

init : Flags -> (ScreenSaverModel, Cmd Msg)
init flags =
  ( { state = Normal
    , idleSeconds = 0
    , charsTyped = []
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

    SS_MouseClick ->
      if amVisible && sceneModel.idleSeconds > 0 then
        -- Note: idleSeconds == 0 means the click was on the scene that segued to here.
        (sceneModel, segueTo Welcome)
      else
        -- It's a mouse click on some other scene, so reset idle time.
        ({sceneModel | idleSeconds=0}, Cmd.none)

    SS_KeyDown code ->
      let
        prevChars = sceneModel.charsTyped
      in
        if amVisible then
          case code of
            219 ->
              -- RFID reader is beginning to send a card number, so clear our buffer.
              ({sceneModel | charsTyped=[]}, Cmd.none)
            221 ->
              -- RFID reader is done sending the card number, so process our buffer.
              handleRfid kioskModel
            32 ->
              -- Spacebar
              (sceneModel, segueTo Welcome)
            c ->
              if c>=48 && c<=57 then
                -- A digit, presumably in the RFID's number. '0' = code 48, '9' = code 57.
                ({sceneModel | charsTyped = Char.fromCode c :: prevChars }, Cmd.none)
              else
                -- Unexpected code.
                (sceneModel, Cmd.none)
        else
          -- It's a key down on some other scene, so reset idle time.
          ({sceneModel | idleSeconds=0}, Cmd.none)

    SS_MemberListResult (Ok {results}) ->
      let
        checkInModel = kioskModel.checkInModel
        member = List.head results
      in
        case member of
          Just m -> (sceneModel, CheckInShortcut m.userName m.id |> CheckInVector |> send)
          Nothing -> (sceneModel, Cmd.none)

    SS_MemberListResult (Err error) ->
      ({sceneModel | state=UnknownRfid, badNews=[toString error]}, Cmd.none)


handleRfid : KioskModel a -> (ScreenSaverModel, Cmd Msg)
handleRfid kioskModel =
  let
    sceneModel = kioskModel.screenSaverModel
    rfidNumber = List.reverse sceneModel.charsTyped |> String.fromList |> String.toInt
    filter = Result.map RfidNumberEquals rfidNumber
    resultHandler = ScreenSaverVector << SS_MemberListResult
    cmd = case filter of
      Ok f -> XisRestApi.getMemberList kioskModel.flags (Just [f]) resultHandler
      Err err -> Cmd.none
  in
    ({sceneModel | state=CheckingRfid}, cmd)


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
    (msg1, msg2, msg3) = case sceneModel.state of
      Normal -> ("Welcome!", "All Visitors Must Sign In", "Tap Spacebar or Screen to Start")
      CheckingRfid -> ("RFID Detected!", "One Moment Please", "We're looking up your details")
      UnknownRfid -> ("Uh Oh!", "RFID was not recognized", "Please let a staffer know")
    beep =
      if sceneModel.state == CheckingRfid then
        audio [src "/static/members/beep-22.mp3", autoplay True] []
      else
        text ""
  in  genericScene kioskModel
    ""
    ""

    (div []
      [ vspace 80
      -- TODO: Do I want to pass all imgs in as flags, as was done with banners?
      , img [src "/static/bzw_ops/WavingHand.gif", logoImgStyle] []
      , vspace 20
      , h1 [h1Style] [text msg1]
      , vspace 0
      , h1 [h1Style] [text msg2]
      , vspace 30
      , h2 [h2Style] [text msg3]
      , beep
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