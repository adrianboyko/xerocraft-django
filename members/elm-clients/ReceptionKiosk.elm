module ReceptionKiosk exposing (..)

import Html exposing (Html, Attribute, a, div, text, span, button, br, p, img)
import Html.Attributes exposing (style, src)
import Regex exposing (regex)

import Material.Textfield as Textfield
import Material.Button as Button
import Material.Toggles as Toggles
import Material
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
  , flexId: String  -- Userid, surname, or email.
  , firstName: String
  , lastName: String
  , email: String
  , isAdult : Bool
  }

init : Flags -> (Model, Cmd Msg)
init f =
  let model =
    Model f.csrfToken f.orgName f.bannerTopUrl f.bannerBottomUrl [Welcome] Material.model "" "" "" "" False
  in
    (model, Cmd.none)

-- reset restores the model as it was after init.
reset : Model -> (Model, Cmd Msg)
reset m =
    init (Flags m.csrfToken m.orgName m.bannerTopUrl m.bannerBottomUrl)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

type Msg
  = Mdl (Material.Msg Msg)  -- For elm-mdl
  | PushScene Scene
  | PopScene
  | GuessIdentity String
  | UpdateFirstName String
  | UpdateLastName String
  | UpdateEmail String
  | ToggleIsAdult

update : Msg -> Model -> (Model, Cmd Msg)
update action model =
  case action of

    Mdl msg2 ->
      Material.update Mdl msg2 model

    PushScene Welcome ->
      -- Segue to "Welcome" is a special case since it re-initializes the scene stack.
      reset model

    PushScene nextScene ->
      -- Push the new scene onto the scene stack.
      ({model | sceneStack = nextScene::model.sceneStack }, Cmd.none)

    PopScene ->
      -- Pop the top scene off the stack.
      ({model | sceneStack = Maybe.withDefault [Welcome] (List.tail model.sceneStack) }, Cmd.none)

    GuessIdentity id ->
      ({model | flexId = id}, Cmd.none)

    UpdateFirstName newVal ->
      ({model | firstName = newVal }, Cmd.none)

    UpdateLastName newVal ->
      ({model | lastName = newVal }, Cmd.none)

    UpdateEmail newVal ->
      ({model | email = newVal }, Cmd.none)

    ToggleIsAdult ->
      ({model | isAdult = not model.isAdult }, Cmd.none)

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

type alias ButtonSpec = { title : String, segue: Scene }

sceneButton : Model -> ButtonSpec -> Html Msg
sceneButton model buttonSpec =
  Button.render Mdl [0] model.mdl
    ([ Button.raised, Options.onClick (PushScene buttonSpec.segue)]++viewButtonCss)
    [ text buttonSpec.title ]

sceneTextField : Model -> Int -> String -> String -> (String -> Msg) -> Html Msg
sceneTextField model index hint value msger =
  Textfield.render Mdl [index] model.mdl
    [ Textfield.label hint
    , Textfield.floatingLabel
    , Textfield.value value
    , Options.onInput msger
    ]
    (text "spam") -- What is this Html Msg argument?

sceneCheckbox : Model -> Int -> String -> Bool -> Msg -> Html Msg
sceneCheckbox model index label value msger =
  -- Toggle.checkbox doesn't seem to handle centering very well. The following div compensates for that.
  div [style ["text-align"=>"left", "display"=>"inline-block", "width"=>"210px"]]
    [ Toggles.checkbox Mdl [index] model.mdl
        [ Options.onToggle msger
        , Toggles.ripple
        , Toggles.value value
        ]
        [ text label ]
    ]

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

vspace : Int -> Html Msg
vspace amount =
  div [style ["height" => (toString amount ++ "px")]] []

sceneView: Model -> String -> String -> Html Msg -> List ButtonSpec -> Html Msg
sceneView model inTitle inSubtitle extraContent buttonSpecs =
  let
    title = replaceAll inTitle "ORGNAME" model.orgName
    subtitle = replaceAll inSubtitle "ORGNAME" model.orgName
  in
    div [navDivStyle]
      [ div [sceneDivStyle]
        [ img [src model.bannerTopUrl, bannerTopStyle] []
        , p [sceneTitleStyle] [text title]
        , p [sceneSubtitleStyle] [text subtitle]
        , extraContent
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
        (text "")
        [ ButtonSpec "First Visit" HaveAcctQ
        , ButtonSpec "Returning" CheckIn
        ]

    HaveAcctQ ->
      sceneView model
        "Great!"
        "Do you already have an account here or on our website?"
        (text "")
        [ ButtonSpec "Yes" CheckIn
        , ButtonSpec "No" LetsCreate
        -- TODO: How about a "I don't know" button, here?
        ]

    CheckIn ->
      sceneView model
        "Let's Get You Checked-In!"
        "Who are you?"
        ( div [] [sceneTextField model 1 "Enter Userid or Surname or Email here" model.flexId GuessIdentity] )
        []  -- No buttons

    LetsCreate ->
      sceneView model
        "Let's Create an Account!"
        "Please tell us about yourself:"
        ( div []
            [ sceneTextField model 2 "Your first name" model.firstName UpdateFirstName
            , vspace 0
            , sceneTextField model 3 "Your last name" model.lastName UpdateLastName
            , vspace 0
            , sceneTextField model 4 "Your email address" model.email UpdateEmail
            , vspace 30
            , sceneCheckbox model 5 "Check if you are 18 or older!" model.isAdult ToggleIsAdult
            , vspace 30
            ]
        )
        [ButtonSpec "OK" ChooseIdAndPw]

    ChooseIdAndPw ->
      sceneView model
        "Id & Password"
        "Please chooose a userid and password for your account:"
        (text "")
        [ButtonSpec "OK" HowDidYouHear]

    HowDidYouHear ->
      sceneView model
        "Just Wondering"
        "How did you hear about us?"
        (text "")
        [ButtonSpec "OK" Waiver]

    Waiver ->
      sceneView model
        "Waiver"
        "Please read the waiver and sign in the box."
        (text "")
        -- TODO: How about a "Clear" choice here?
        [ButtonSpec "Accept" Rules]

    Rules ->
      sceneView model
        "Rules"
        "Please read the rules and check the box to agree."
        (text "")
        [ButtonSpec "I Agree" Activity]

    Activity ->
      sceneView model
        "Today's Activity?"
        "Let us know what you'll be doing:"
        (text "")
        [ButtonSpec "OK" SupportUs]

    SupportUs ->
      sceneView model
        "Please Support Us!"
        "{TODO}"
        (text "")
        [ButtonSpec "OK" Done]

    Done ->
      sceneView model
        "You're Checked In"
        "Have fun!"
        (text "")
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
  , "margin-top" => "5%"
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