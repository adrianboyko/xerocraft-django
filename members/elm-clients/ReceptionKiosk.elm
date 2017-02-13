module ReceptionKiosk exposing (..)

import Html exposing (Html, Attribute, a, div, text, span, button, br, p, img)
import Html.Attributes exposing (style, src)
import Regex exposing (regex)

import Material
import Material.Button as Button
import Material.Options as Options exposing (css)

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
-- Utilities
-----------------------------------------------------------------------------

replaceAll : String -> String -> String -> String
replaceAll theString oldSub newSub =
  Regex.replace Regex.All (regex oldSub ) (\_ -> newSub) theString


-----------------------------------------------------------------------------
-- MODEL
-----------------------------------------------------------------------------

-- These are params from the server. Elm docs tend to call them "flags".
type alias Flags =
  { csrfToken: String
  , orgName: String
  , bannerTopUrl: String
  , bannerBottomUrl: String
  }

type Scene
  = Welcome
  | HaveAcctQ
  | CheckIn
  | LetsCreate
  | ChooseIdAndPw
  | HowDidYouHear
  | Waiver
  | Rules
  | Activity
  | SupportUs
  | Done

type alias Model =
  { csrfToken: String
  , orgName: String
  , bannerTopUrl: String
  , bannerBottomUrl: String
  , sceneStack: List Scene  -- 1st element is the top of the stack
  , mdl: Material.Model
  }

init : Flags -> (Model, Cmd Msg)
init f =
  let model =
    Model f.csrfToken f.orgName f.bannerTopUrl f.bannerBottomUrl [Welcome] Material.model
  in
    (model, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

type Msg
  = Mdl (Material.Msg Msg)  -- For elm-mdl
  | PushScene Scene
  | PopScene

update : Msg -> Model -> (Model, Cmd Msg)
update action model =
  case action of

    Mdl msg2 ->
      Material.update Mdl msg2 model

    PushScene Welcome ->
      -- Segue to "Welcome" is a special case since it re-initializes the scene stack.
      ({model | sceneStack = [Welcome] }, Cmd.none)

    PushScene nextScene ->
      -- Push the new scene onto the scene stack.
      ({model | sceneStack = nextScene::model.sceneStack }, Cmd.none)

    PopScene ->
      -- Pop the top scene off the stack.
      ({model | sceneStack = Maybe.withDefault [Welcome] (List.tail model.sceneStack) }, Cmd.none)

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

type alias ButtonSpec = { title : String, segue: Scene }

sceneButton : Model -> ButtonSpec -> Html Msg
sceneButton model buttonSpec =
  Button.render Mdl [0] model.mdl
    ([ Button.raised, Options.onClick (PushScene buttonSpec.segue)]++viewButtonCss)
    [ text buttonSpec.title ]

backButton : Model -> Html Msg
backButton model =
  if List.length model.sceneStack > 1
  then
    div []
      [ Button.render Mdl [0] model.mdl
          ([Button.flat, Options.onClick PopScene]++navButtonCss)
          [text "Back"]
      , Button.render Mdl [0] model.mdl
          ([Button.flat, Options.onClick (PushScene Welcome)]++navButtonCss)
          [text "Quit"]
      ]
    else
      text ""

sceneView: Model -> String -> String -> List ButtonSpec -> Html Msg
sceneView model inTitle inSubtitle buttonSpecs =
  let
    title = replaceAll inTitle "ORGNAME" model.orgName
    subtitle = replaceAll inSubtitle "ORGNAME" model.orgName
  in
    div [navDivStyle]
      [ div [sceneDivStyle]
        [ img [src model.bannerTopUrl, bannerTopStyle] []
        , p [sceneTitleStyle] [text title]
        , p [sceneSubtitleStyle] [text subtitle]
        , div [] (List.map (sceneButton model) buttonSpecs)
        , img [src model.bannerBottomUrl, bannerBottomStyle] []
        ]
      , backButton model
      ]

view : Model -> Html Msg
view model =

  -- Default of "Welcome" elegantly guards against stack underflow, which should not occur.
  case Maybe.withDefault Welcome (List.head model.sceneStack) of

    Welcome ->
      sceneView model
        "Welcome!"
        "Is this your first visit?"
        [ ButtonSpec "Yes" HaveAcctQ
        , ButtonSpec "No" CheckIn
        ]

    HaveAcctQ ->
      sceneView model
        "Great!"
        "Do you already have an account here or on our website?"
        [ ButtonSpec "Yes" CheckIn
        , ButtonSpec "No" LetsCreate
        -- TODO: How about a "I don't know" button, here?
        ]

    CheckIn ->
      sceneView model
        "Please Check In"
        "Enter your userid or email address:"
        [ButtonSpec "OK" Waiver]

    LetsCreate ->
      sceneView model
        "Let's Create One!"
        "Please tell us about yourself:"
        [ButtonSpec "OK" ChooseIdAndPw]

    ChooseIdAndPw ->
      sceneView model
        "Id & Password"
        "Please chooose a userid and password for your account:"
        [ButtonSpec "OK" HowDidYouHear]

    HowDidYouHear ->
      sceneView model
        "Just Wondering"
        "How did you hear about us?"
        [ButtonSpec "OK" Waiver]

    Waiver ->
      sceneView model
        "Waiver"
        "Please read the waiver and sign in the box."
        -- TODO: How about a "Clear" choice here?
        [ButtonSpec "Accept" Rules]

    Rules ->
      sceneView model
        "Rules"
        "Please read the rules and check the box to agree."
        [ButtonSpec "I Agree" Activity]

    Activity ->
      sceneView model
        "Today's Activity?"
        "Let us know what you'll be doing:"
        [ButtonSpec "OK" SupportUs]

    SupportUs ->
      sceneView model
        "Please Support Us!"
        "{TODO}"
        [ButtonSpec "OK" Done]

    Done ->
      sceneView model
        "You're Checked In"
        "Have fun!"
        [ButtonSpec "Yay!" Welcome]


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------

subscriptions: Model -> Sub Msg
subscriptions model =
  Sub.batch
    [
    ]

-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

(=>) = (,)

sceneWidth = "640px"

navDivStyle = style
  [ "font-family" => "Roboto Condensed, Arial, Helvetica"
  , "text-align" => "center"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "margin-top" => "10%"
  , "width" => sceneWidth
  ]

sceneDivStyle = style
  [ "border" => "1px solid #bbbbbb"
  , "background-color" => "white"
  , "padding" => "0px"
  ]

sceneTitleStyle = style
  [ "font-size" => "22pt"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "margin-top" => "50px"
  , "margin-bottom" => "0.25em"
  ]

sceneSubtitleStyle = style
  [ "font-size" => "16pt"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "margin-top" => "0"
  ]

bannerTopStyle = style
  [ "width" => sceneWidth
  , "margin" => "0"
  ]

bannerBottomStyle = style
  [ "width" => sceneWidth
  , "margin-top" => "50px"
  ]

viewButtonCss =
  [ css "margin-left" "10px"
  , css "margin-right" "10px"
  , css "padding-top" "25px"
  , css "padding-bottom" "55px"
  , css "padding-left" "30px"
  , css "padding-right" "30px"
  , css "font-size" "14pt"
  ]

navButtonCss =
  [ css "margin-left" "5px"
  , css "margin-right" "5px"
  , css "margin-top" "20px"
  , css "font-size" "9pt"
  ]