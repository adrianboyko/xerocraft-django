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

type Step
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
  , step: Step
  , mdl: Material.Model
  }

init : Flags -> (Model, Cmd Msg)
init f =
  let model =
    Model f.csrfToken f.orgName f.bannerTopUrl f.bannerBottomUrl Welcome Material.model
  in
    (model, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

type Msg
  = Mdl (Material.Msg Msg)  -- For elm-mdl
  | Segue Step

update : Msg -> Model -> (Model, Cmd Msg)
update action model =
  case action of

    Mdl msg2 ->
      Material.update Mdl msg2 model

    Segue nextStep ->
      ({model | step=nextStep }, Cmd.none)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

type alias ButtonSpec = { title : String, segue: Step }

dialogButton : Model -> ButtonSpec -> Html Msg
dialogButton model buttonSpec =
  Button.render Mdl [0] model.mdl
    ([ Button.raised, Options.onClick (Segue buttonSpec.segue)]++dlgButtonCss)
    [ text buttonSpec.title ]

stepDialog: Model -> String -> String -> List ButtonSpec -> Html Msg
stepDialog model inTitle inSubtitle buttonSpecs =
  let
    title = replaceAll inTitle "ORGNAME" model.orgName
    subtitle = replaceAll inSubtitle "ORGNAME" model.orgName
  in
    div [stepDialogStyle]
      [ img [src model.bannerTopUrl, bannerTopStyle] []
      , p [stepTitleStyle] [text title]
      , p [stepSubtitleStyle] [text subtitle]
      , div [] (List.map (dialogButton model) buttonSpecs)
      , img [src model.bannerBottomUrl, bannerBottomStyle] []
      ]

view : Model -> Html Msg
view model =
  case model.step of

    Welcome ->
      stepDialog model
        "Welcome!"
        "Is this your first visit?"
        [ ButtonSpec "Yes" HaveAcctQ
        , ButtonSpec "No" CheckIn
        ]

    HaveAcctQ ->
      stepDialog model
        "Great!"
        "Do you already have an account here or on our website?"
        [ ButtonSpec "Yes, I do" CheckIn
        , ButtonSpec "No, I don't" LetsCreate
        -- TODO: How about a "I don't know" button, here?
        ]

    CheckIn ->
      stepDialog model
        "Please Check In"
        "Enter your userid or email address:"
        [ButtonSpec "OK" Waiver]

    LetsCreate ->
      stepDialog model
        "Let's Create One!"
        "Please tell us about yourself:"
        [ButtonSpec "OK" ChooseIdAndPw]

    ChooseIdAndPw ->
      stepDialog model
        "Id & Password"
        "Please chooose a userid and password for your account:"
        [ButtonSpec "OK" HowDidYouHear]

    HowDidYouHear ->
      stepDialog model
        "Just Wondering"
        "How did you hear about us?"
        [ButtonSpec "OK" Waiver]

    Waiver ->
      stepDialog model
        "Waiver"
        "Please read the waiver and sign in the box."
        -- TODO: How about a "Clear" choice here?
        [ButtonSpec "Accept" Rules]

    Rules ->
      stepDialog model
        "Rules"
        "Please read the rules and check the box to agree."
        [ButtonSpec "I Agree" Activity]

    Activity ->
      stepDialog model
        "Today's Activity?"
        "Let us know what you'll be doing:"
        [ButtonSpec "OK" SupportUs]

    SupportUs ->
      stepDialog model
        "Please Support Us!"
        "{TODO}"
        [ButtonSpec "OK" Done]

    Done ->
      stepDialog model
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

dialogWidth = "640px"

stepDialogStyle = style
  [ "font-family" => "Roboto Condensed, Arial, Helvetica"
  , "text-align" => "center"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "margin-top" => "10%"
  , "width" => dialogWidth
  , "border" => "1px solid #bbbbbb"
  , "background-color" => "white"
  , "padding" => "0px"
  ]

stepTitleStyle = style
  [ "font-size" => "22pt"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "margin-top" => "50px"
  , "margin-bottom" => "0.25em"
  ]

stepSubtitleStyle = style
  [ "font-size" => "16pt"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "margin-top" => "0"
  ]

bannerTopStyle = style
  [ "width" => dialogWidth
  , "margin" => "0"
  ]

bannerBottomStyle = style
  [ "width" => dialogWidth
  , "margin-top" => "50px"
  ]

dlgButtonCss =
  [ css "margin-left" "10px"
  , css "margin-right" "10px"
  , css "padding-top" "25px"
  , css "padding-bottom" "55px"
  , css "padding-left" "30px"
  , css "padding-right" "30px"
  , css "font-size" "14pt"
  ]