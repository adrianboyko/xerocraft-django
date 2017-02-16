module ReceptionKiosk exposing (..)

import Html exposing (Html, Attribute, a, div, text, span, button, br, p, img)
import Html.Attributes exposing (style, src)
import Regex exposing (regex)
import Http
import Task
import Json.Decode as Dec
import Json.Encode as Enc

import Material.Textfield as Textfield
import Material.Button as Button
import Material.Toggles as Toggles
import Material.Chip as Chip
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
  | ChooseUserNameAndPw
  | HowDidYouHear
  | Waiver
  | Rules
  | Activity
  | SupportUs
  | Done

type alias Acct =
  { userName: String
  , password: String
  , memberNum: Maybe Int
  , firstName: String
  , lastName: String
  , email: String
  , isAdult: Bool
  }

type alias MatchingAcct =
  { userName: String
  , memberNum: Int
  }

type alias MatchingAcctInfo =
  { target: String
  , matches: List MatchingAcct
  }

blankAcct : Acct
blankAcct = Acct
    ""
    ""
    Nothing
    ""
    ""
    ""
    False

type alias Model =
  { csrfToken: String
  , orgName: String
  , bannerTopUrl: String
  , bannerBottomUrl: String
  , sceneStack: List Scene  -- 1st element is the top of the stack
  , mdl: Material.Model
  , flexId: String  -- UserName, surname, or email.
  , visitor: Acct
  , matches: List MatchingAcct
  , error: Maybe String
  }

init : Flags -> (Model, Cmd Msg)
init f =
  ( Model
      f.csrfToken
      f.orgName
      f.bannerTopUrl
      f.bannerBottomUrl
      [Welcome]
      Material.model
      ""
      blankAcct
      []
      Nothing
  , Cmd.none
  )

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
  | UpdateFlexId String
  | UpdateFirstName String
  | UpdateLastName String
  | UpdateEmail String
  | ToggleIsAdult
  | UpdateUserName String
  | UpdatePassword String
  | UpdateMatchingAccts (Result Http.Error MatchingAcctInfo)
  | LogCheckIn Int

findMatchingAccts : Model -> String -> Html Msg
findMatchingAccts model flexId =
    div [] []

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

    UpdateFlexId id ->
      if (String.length id) > 1
      then
        let
          url = "/members/reception/matching-accts/"++id++"/"  -- TODO: Django-ize the id.
          request = Http.get url decodeMatchingAcctInfo
          cmd = Http.send UpdateMatchingAccts request
        in
          ({model | flexId = id}, cmd)
      else
        ({model | matches = [], flexId = id}, Cmd.none )


    UpdateFirstName newVal ->
      let v = model.visitor  -- This is necessary because of a bug in PyCharm elm plugin.
      in ({model | visitor = {v | firstName = newVal }}, Cmd.none)

    UpdateLastName newVal ->
      let v = model.visitor  -- This is necessary because of a bug in PyCharm elm plugin.
      in ({model | visitor = {v | lastName = newVal }}, Cmd.none)

    UpdateEmail newVal ->
      let v = model.visitor  -- This is necessary because of a bug in PyCharm elm plugin.
      in ({model | visitor = {v | email = newVal }}, Cmd.none)

    ToggleIsAdult ->
      let v = model.visitor  -- This is necessary because of a bug in PyCharm elm plugin.
      in ({model | visitor = {v | isAdult = not v.isAdult }}, Cmd.none)

    UpdateUserName newVal ->
      let v = model.visitor  -- This is necessary because of a bug in PyCharm elm plugin.
      in ({model | visitor = {v | userName = newVal }}, Cmd.none)

    UpdatePassword newVal ->
      let v = model.visitor  -- This is necessary because of a bug in PyCharm elm plugin.
      in ({model | visitor = {v | password = newVal }}, Cmd.none)

    UpdateMatchingAccts (Ok {target, matches}) ->
      if target == model.flexId
      then ({model | matches = matches, error = Nothing}, Cmd.none)
      else (model, Cmd.none)

    UpdateMatchingAccts (Err error) ->
      ({model | error = Just (toString error)}, Cmd.none)

    LogCheckIn memberNum ->
      (model, Cmd.none)

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
    , css "width" "500px"
    ]
    (text "spam") -- What is this Html Msg argument?

scenePasswordField : Model -> Int -> String -> String -> (String -> Msg) -> Html Msg
scenePasswordField model index hint value msger =
  Textfield.render Mdl [index] model.mdl
    [ Textfield.label hint
    , Textfield.password
    , Textfield.floatingLabel
    , Textfield.value value
    , Options.onInput msger
    ]
    (text "spam") -- What is this Html Msg argument?

sceneCheckbox : Model -> Int -> String -> Bool -> Msg -> Html Msg
sceneCheckbox model index label value msger =
  -- Toggle.checkbox doesn't seem to handle centering very well. The following div compensates for that.
  div [style ["text-align"=>"left", "display"=>"inline-block", "width"=>"400px"]]
    [ Toggles.checkbox Mdl [index] model.mdl
        [ Options.onToggle msger
        , Toggles.ripple
        , Toggles.value value
        ]
        [span [style ["font-size"=>"24pt"]] [ text label ]]
    ]

navButtons : Model -> Html Msg
navButtons model =
  if List.length model.sceneStack > 1
  then
    div [navDivStyle]
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
    canvasView model
      [ p [sceneTitleStyle] [text title]
      , p [sceneSubtitleStyle] [text subtitle]
      , extraContent
      , vspace 50
      , div [] (List.map (sceneButton model) buttonSpecs)
      , navButtons model
      , case model.error of
          Just err -> text err
          Nothing -> text ""
      ]

canvasView: Model -> List (Html Msg) -> Html Msg
canvasView model scene =
  div [canvasDivStyle]
    [ img [src model.bannerTopUrl, bannerTopStyle] []
    , div [sceneDivStyle] scene
--    , navButtons model
    , img [src model.bannerBottomUrl, bannerBottomStyle] []
    ]

howDidYouHearChoices : Model -> Html Msg
howDidYouHearChoices model =
  text ""

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
        ( div []
            (List.concat
              [ [sceneTextField model 1 "Your Username or Surname" model.flexId UpdateFlexId, vspace 0]
              , List.map (\acct -> Chip.button [Options.onClick (LogCheckIn acct.memberNum)] [ Chip.content [] [ text acct.userName]]) model.matches
              ]
            )
        )
        []  -- No buttons

    LetsCreate ->
      sceneView model
        "Let's Create an Account!"
        "Please tell us about yourself:"
        ( div []
            [ sceneTextField model 2 "Your first name" model.visitor.firstName UpdateFirstName
            , vspace 0
            , sceneTextField model 3 "Your last name" model.visitor.lastName UpdateLastName
            , vspace 0
            , sceneTextField model 4 "Your email address" model.visitor.email UpdateEmail
            , vspace 30
            , sceneCheckbox model 5 "Check if you are 18 or older!" model.visitor.isAdult ToggleIsAdult
            ]
        )
        [ButtonSpec "OK" ChooseUserNameAndPw]

    ChooseUserNameAndPw ->
      sceneView model
        "Id & Password"
        "Please chooose a user name and password for your account:"
        ( div []
            [ sceneTextField model 6 "Choose a user name" model.visitor.userName UpdateUserName
            , vspace 0
            , scenePasswordField model 7 "Choose a password" model.visitor.password UpdatePassword
            ]
        )
        [ButtonSpec "OK" HowDidYouHear]

    HowDidYouHear ->
      sceneView model
        "Just Wondering"
        "How did you hear about us?"
        (howDidYouHearChoices model)
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
-- JSON
-----------------------------------------------------------------------------

decodeMatchingAcct : Dec.Decoder MatchingAcct
decodeMatchingAcct =
  Dec.map2 MatchingAcct
    (Dec.field "userName" Dec.string)
    (Dec.field "memberNum" Dec.int)

decodeMatchingAcctInfo : Dec.Decoder MatchingAcctInfo
decodeMatchingAcctInfo =
  Dec.map2 MatchingAcctInfo
    (Dec.field "target" Dec.string)
    (Dec.field "matches" (Dec.list decodeMatchingAcct))


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

(=>) = (,)

-- The reception kiosk is being designed to run full-screen on Motorola Xooms.
-- These have resolution 1280 x 800 at about 150ppi.
-- When testing on desktop, the scene should be about 13.6cm wide.

sceneWidth = "800px"
sceneHeight = "1280px"
topBannerHeight = "155px"
bottomBannerHeight = "84px"

canvasDivStyle = style
  [ "font-family" => "Roboto Condensed, Arial, Helvetica"
  , "text-align" => "center"
  , "padding-left" => "0"
  , "padding-right" => "0"
  , "padding-top" => topBannerHeight
  , "padding-bottom" => bottomBannerHeight
  , "position" => "absolute"
  , "top" => "0"
  , "bottom" => "0"
  , "left" => "0"
  , "right" => "0"
  ]

sceneDivStyle = style
  [ "margin-left" => "auto"
  , "margin-right" => "auto"
  , "border" => "1px solid #bbbbbb"
  , "background-color" => "white"
  , "width" => sceneWidth
  , "min-height" => "99.8%"
  ]

sceneTitleStyle = style
  [ "font-size" => "32pt"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "margin-top" => "2em"
  , "margin-bottom" => "0.5em"
  ]

sceneSubtitleStyle = style
  [ "font-size" => "24pt"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "margin-bottom" => "1em"
  , "margin-top" => "0"
  ]

bannerTopStyle = style
  [ "display" => "block"
  , "margin-top" => ("-"++topBannerHeight)
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "height" => topBannerHeight
  , "width" => sceneWidth
  ]

bannerBottomStyle = style
  [ "display" => "block"
  , "margin-bottom" => ("-"++bottomBannerHeight)
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "height" => bottomBannerHeight
  , "width" => sceneWidth
  ]

viewButtonCss =
  [ css "margin-left" "10px"
  , css "margin-right" "10px"
  , css "padding-top" "25px"
  , css "padding-bottom" "55px"
  , css "padding-left" "30px"
  , css "padding-right" "30px"
  , css "font-size" "18pt"
  ]

navDivStyle = style
  [ "display" => "block"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "width" => sceneWidth
  ]

navButtonCss =
  [ css "margin-left" "120px"
  , css "margin-right" "120px"
  , css "margin-top" "100px"
  , css "font-size" "14pt"
  , css "font-color" "#dddddd"
  ]

sceneChipCss =
  [ css "margin-left" "3px"
  , css "margin-right" "3px"
  ]
