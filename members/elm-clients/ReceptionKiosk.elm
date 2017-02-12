module ReceptionKiosk exposing (..)

import Html exposing (Html, Attribute, a, div, table, tr, td, th, text, span, button, br, p)
import Regex exposing (regex)

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
  }

type Step
  = Welcome
  | HaveAcct
  | CheckIn
  | LetsCreate
  | UserIdAndPw
  | HowDidYouHear
  | Waiver
  | Rules
  | Activity
  | SupportUs
  | Done

type alias Model =
  { csrfToken: String
  , orgName: String
  , step: Step
  }

type Msg = Spam

init : Flags -> (Model, Cmd Msg)
init {csrfToken, orgName} =
  ( Model csrfToken orgName Welcome, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : Msg -> Model -> (Model, Cmd Msg)
update action model =
  case action of

    Spam -> (model, Cmd.none)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

stepDialog: Model -> String -> String -> Html Msg
stepDialog model inTitle inSubtitle =
  let
    title = replaceAll inTitle "ORGNAME" model.orgName
    subtitle = replaceAll inSubtitle "ORGNAME" model.orgName
  in
    div []
      [ text title
      , br [] []
      , text subtitle
      ]

view : Model -> Html Msg
view model =
  case model.step of

    Welcome ->
      stepDialog model
        "Welcome to ORGNAME!"
        "Is this your first visit?"

    HaveAcct ->
      stepDialog model
        "Great!"
        "Do you already have an account here or on our website?"

    CheckIn ->
      stepDialog model
        "Please Check In"
        "Enter your userid or email address:"

    LetsCreate ->
      stepDialog model
        "Let's Create One!"
        "Please tell us about yourself:"

    UserIdAndPw ->
      stepDialog model
        "Id & Password"
        "Please chooose a userid and password for your account:"

    HowDidYouHear ->
      stepDialog model
        "Just Wondering"
        "How did you hear about ORGNAME"

    Waiver ->
      stepDialog model
        "Waiver"
        "Please read the waiver and sign in the box to accept."

    Rules ->
      stepDialog model
        "Rules"
        "Please read the rules and check the box to agree."

    Activity ->
      stepDialog model
        "Today's Activity?"
        "Let us know what you'll be doing:"

    SupportUs ->
      stepDialog model
        "Support ORGNAME"
        "{TODO}"

    Done ->
      stepDialog model
        "You're Checked In"
        "Have fun!"


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------

subscriptions: Model -> Sub Msg
subscriptions model =
  Sub.batch
    [
    ]
