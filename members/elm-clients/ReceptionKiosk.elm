port module ReceptionKiosk exposing (..)

import Html exposing (Html, Attribute, a, div, text, span, button, br, p, img, h1, h2, ol, li, b, canvas)
import Html.Attributes exposing (style, src, id, tabindex, width, height)
import Regex exposing (regex)
import Http
import Task
import Json.Decode as Dec
import Json.Encode as Enc

import Update.Extra.Infix exposing ((:>))

import Json.Decode.Pipeline exposing (decode, required, hardcoded)

import List.Extra

import Material.Textfield as Textfield
import Material.Button as Button
import Material.Toggles as Toggles
import Material.Chip as Chip
import Material.Options as Options exposing (css)
import Material.List as Lists
import Material


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

djangoizeId : String -> String
djangoizeId rawId =
  -- TODO: Replacing spaces handles 90% of cases, but need to handle other forbidden chars.
  replaceAll rawId " " "_"


-----------------------------------------------------------------------------
-- MODEL
-----------------------------------------------------------------------------

-- These are params from the server. Elm docs tend to call them "flags".
type alias Flags =
  { csrfToken: String
  , orgName: String
  , bannerTopUrl: String
  , bannerBottomUrl: String
  , discoveryMethodsUrl: String
  }

type Scene
  = Welcome
  | HaveAcctQ
  | CheckIn
  | LetsCreate
  | ChooseUserNameAndPw
  | HowDidYouHear
  | Waiver
  | Activity
  | Done
  | AnyScene  -- This is a pseudo scene, not an actual visual scene.

type alias DiscoveryMethod =
  { id: Int
  , name: String
  , order: Int
  , selected: Bool
  }

type alias DiscoveryMethodInfo =
  { count: Int
  , next: Maybe String
  , previous: Maybe String
  , results: List DiscoveryMethod
  }

type alias Acct =
  { userName: String
  , password: String
  , password2: String  -- The password retyped.
  , memberNum: Maybe Int
  , firstName: String
  , lastName: String
  , email: String
  , isAdult: Bool
  , signature : String  -- This is a data URL
  }

blankAcct : Acct
blankAcct =
  { userName = ""
  , password = ""
  , password2 = ""
  , memberNum = Nothing
  , firstName = ""
  , lastName = ""
  , email = ""
  , isAdult = False
  , signature = ""
  }

type alias MatchingAcct =
  { userName: String
  , memberNum: Int
  }

type alias MatchingAcctInfo =
  { target: String
  , matches: List MatchingAcct
  }

type ReasonForVisit
  = Curiousity
  | ClassParticipant
  | MemberPrivileges
  | GuestOfMember
  | Volunteer
  | Other

reasonString : Model -> ReasonForVisit -> String
reasonString model reason =
  case reason of
    Curiousity -> "Checking out " ++ model.orgName
    ClassParticipant -> "Attending a class or workshop"
    MemberPrivileges -> "Working on a personal project"
    GuestOfMember -> "Guest of a paying member"
    Volunteer -> "Volunteering or staffing"
    Other -> "Other"

type alias Model =
  { csrfToken: String
  , orgName: String
  , bannerTopUrl: String
  , bannerBottomUrl: String
  , discoveryMethodsUrl: String
  , sceneStack: List Scene  -- 1st element is the top of the stack
  , mdl: Material.Model
  , flexId: String  -- UserName, surname, or email.
  , visitor: Acct
  , matches: List MatchingAcct  -- Matches to username/surname
  , discoveryMethods: List DiscoveryMethod  -- Fetched from backend
  , isSigning: Bool
  , reasonForVisit: Maybe ReasonForVisit
  , validationMessages: List String
  , error: Maybe String
  }

init : Flags -> (Model, Cmd Msg)
init f =
  ( Model
      f.csrfToken
      f.orgName
      f.bannerTopUrl
      f.bannerBottomUrl
      f.discoveryMethodsUrl
      [Welcome]
      Material.model
      ""
      blankAcct
      []
      []
      False
      Nothing
      []
      Nothing
  , Cmd.none
  )

-- reset restores the model as it was after init.
reset : Model -> (Model, Cmd Msg)
reset m =
    init (Flags m.csrfToken m.orgName m.bannerTopUrl m.bannerBottomUrl m.discoveryMethodsUrl)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

type Msg
  = Mdl (Material.Msg Msg)  -- For elm-mdl
  | PushScene Scene
  | PopScene
  | AfterSceneChangeTo Scene
  | UpdateFlexId String
  | UpdateFirstName String
  | UpdateLastName String
  | UpdateEmail String
  | ToggleIsAdult
  | UpdateUserName String
  | UpdatePassword String
  | UpdatePassword2 String
  | UpdateMatchingAccts (Result Http.Error MatchingAcctInfo)
  | LogCheckIn Int
  | AccDiscoveryMethods (Result Http.Error DiscoveryMethodInfo)  -- "Acc" means "accumulate"
  | ToggleDiscoveryMethod DiscoveryMethod
  | ShowSignaturePad String
  | ClearSignaturePad String
  | UpdateReasonForVisit ReasonForVisit
  | ValidateUserIdAndPw
  | ValidateUserNameUniqueness (Result Http.Error MatchingAcctInfo)
  | GetSignature
  | UpdateSignature String  -- String is a data URL representation of an image.

port initSignaturePad : (String, String) -> Cmd msg  -- 1) ID of canvas to be used, 2) data URL of image or ""
port clearSignaturePad : String -> Cmd msg
port sendSignatureImage : String -> Cmd msg  -- "image/png", "image/jpeg", or "image/svg+xml"
port signatureImage : (String -> msg) -> Sub msg  -- requested signature data arrives via this port

update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
  case msg of

    Mdl msg2 ->
      Material.update Mdl msg2 model

    PushScene Welcome ->
      -- Segue to "Welcome" is a special case since it resets the model.
      reset model

    PushScene nextScene ->
      -- Push the new scene onto the scene stack.
      let
        newModel = {model | sceneStack = nextScene::model.sceneStack }
      in
        (newModel, Cmd.none) :> update (AfterSceneChangeTo nextScene)

    PopScene ->
      -- Pop the top scene off the stack.
      let
        newModel = {model | sceneStack = Maybe.withDefault [Welcome] (List.tail model.sceneStack) }
        newScene = Maybe.withDefault Welcome (List.head newModel.sceneStack)
      in
        (newModel, Cmd.none) :> update (AfterSceneChangeTo newScene)

    AfterSceneChangeTo LetsCreate ->
      -- This is a good place to start fetching the "discovery methods" from backend.
      let
        url = model.discoveryMethodsUrl ++ "?format=json"  -- Easier than an "Accept" header.
        request = Http.get url decodeDiscoveryMethodInfo
        cmd =
          if List.length model.discoveryMethods == 0
          then Http.send AccDiscoveryMethods request
          else Cmd.none -- Don't fetch if we already have them. Can happen with backward scene navigation.
      in
        (model, cmd) :> update (AfterSceneChangeTo AnyScene)

    AfterSceneChangeTo Waiver ->
      ({model | isSigning=False}, Cmd.none) :> update (AfterSceneChangeTo AnyScene)

    AfterSceneChangeTo newScene ->
      -- Default action is to clear out any validation messages.
      ({model | validationMessages = []}, Cmd.none)

    UpdateFlexId rawId ->
      let id = djangoizeId rawId
      in
        if (String.length id) > 1
        then
          let
            url = "/members/reception/matching-accts/"++id++"/"
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

    UpdatePassword2 newVal ->
      let v = model.visitor  -- This is necessary because of a bug in PyCharm elm plugin.
      in ({model | visitor = {v | password2 = newVal }}, Cmd.none)

    UpdateMatchingAccts (Ok {target, matches}) ->
      if target == model.flexId
      then ({model | matches = matches, error = Nothing}, Cmd.none)
      else (model, Cmd.none)

    UpdateMatchingAccts (Err error) ->
      ({model | error = Just (toString error)}, Cmd.none)

    LogCheckIn memberNum ->
      -- TODO: Log the visit. Might be last feature to be implemented to avoid collecting bogus visits during alpha testing.
      (model, Cmd.none) :> update (PushScene Activity)

    AccDiscoveryMethods (Ok {count, next, previous, results}) ->
      -- Data from backend might be paged, so we need to accumulate the batches as they come.
      let
        methods = model.discoveryMethods ++ results
      in
        -- Also need to deal with "next", if it's not Nothing.
        ({model | discoveryMethods = methods}, Cmd.none)

    AccDiscoveryMethods (Err error) ->
      ({model | error = Just (toString error)}, Cmd.none)

    ToggleDiscoveryMethod dm ->
      let
        replace = List.Extra.replaceIf
        picker = \x -> x.id == dm.id
        replacement = { dm | selected = not dm.selected }
      in
        -- TODO: This should also add/remove the discovery method choice on the backend.
        ({model | discoveryMethods = replace picker replacement model.discoveryMethods}, Cmd.none)

    ShowSignaturePad canvasId ->
      ({model | isSigning=True}, initSignaturePad (canvasId, model.visitor.signature))

    ClearSignaturePad canvasId ->
      (model, clearSignaturePad canvasId)

    UpdateReasonForVisit reason ->
      ({model | reasonForVisit = Just reason}, Cmd.none)

    ValidateUserIdAndPw ->
      validateUserIdAndPw model

    ValidateUserNameUniqueness result ->
      validateUserNameUniqueness model result

    GetSignature ->
      (model, sendSignatureImage "image/png")

    UpdateSignature dataUrl ->
      let
        v = model.visitor  -- This is necessary because of a bug in PyCharm elm plugin.
        newModel = {model | visitor = {v | signature = dataUrl }}
      in
        -- TODO: Should create account here.
        (newModel, Cmd.none) :> update (PushScene Activity)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : Model -> Html Msg
view model =
  -- Default of "Welcome" elegantly guards against stack underflow, which should not occur.
  case Maybe.withDefault Welcome (List.head model.sceneStack) of

    Welcome -> welcomeScene model
    HaveAcctQ -> haveAcctScene model
    CheckIn -> checkInScene model
    LetsCreate -> letsCreateScene model
    ChooseUserNameAndPw -> chooseUserNameAndPwScene model
    HowDidYouHear -> howDidYouHearScene model
    Waiver -> waiverScene model
    Activity -> activityScene model
    Done -> doneScene model
    AnyScene -> text ""  -- We will never get here. "AnyScene" is a pseudo scene.

-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

wizardView: Model -> List (Html Msg) -> Html Msg
wizardView model scene =
  div [canvasDivStyle]
    [ img [src model.bannerTopUrl, bannerTopStyle] []
    , div [sceneDivStyle] scene
    , wizardNavButtons model
    , img [src model.bannerBottomUrl, bannerBottomStyle] []
    ]

wizardNavButtons : Model -> Html Msg
wizardNavButtons model =
  div [navDivStyle]
    (
    if List.length model.sceneStack > 1
    then
      [ Button.render Mdl [10000] model.mdl
          ([Button.flat, Options.onClick PopScene]++navButtonCss)
          [text "Back"]
      , hspace 600
      , Button.render Mdl [10001] model.mdl
          ([Button.flat, Options.onClick (PushScene Welcome)]++navButtonCss)
          [text "Quit"]
      ]
    else
      [text ""]
    )

-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

genericSceneView: Model -> String -> String -> Html Msg -> List ButtonSpec -> Html Msg
genericSceneView model title subtitle extraContent buttonSpecs =
  wizardView model
    [ p [sceneTitleStyle] [text title]
    , p [sceneSubtitleStyle] [text subtitle]
    , extraContent
    , vspace 50
    , div [] (List.map (sceneButton model) buttonSpecs)
    , case model.error of
        Just err -> text err
        Nothing -> text ""
    ]

type alias ButtonSpec = { title : String, msg: Msg }
sceneButton : Model -> ButtonSpec -> Html Msg
sceneButton model buttonSpec =
  Button.render Mdl [0] model.mdl
    ([ Button.raised, (Options.onClick buttonSpec.msg)]++viewButtonCss)
    [ text buttonSpec.title ]

sceneGenericTextField : Model -> Int -> String -> String -> (String -> Msg) -> List (Textfield.Property Msg) -> Html Msg
sceneGenericTextField model index hint value msger options =
  Textfield.render Mdl [index] model.mdl
    ( [ Textfield.label hint
      , Textfield.floatingLabel
      , Textfield.value value
      , Options.onInput msger
      , css "width" "500px"
      ]
    ++ options
    )
    (text "spam") -- What is this Html Msg argument?

sceneTextField : Model -> Int -> String -> String -> (String -> Msg) -> Html Msg
sceneTextField model index hint value msger =
  sceneGenericTextField model index hint value msger []

scenePasswordField : Model -> Int -> String -> String -> (String -> Msg) -> Html Msg
scenePasswordField model index hint value msger =
  sceneGenericTextField model index hint value msger [Textfield.password]

sceneEmailField : Model -> Int -> String -> String -> (String -> Msg) -> Html Msg
sceneEmailField model index hint value msger =
  sceneGenericTextField model index hint value msger [Textfield.email]

sceneCheckbox : Model -> Int -> String -> Bool -> Msg -> Html Msg
sceneCheckbox model index label value msger =
  -- Toggle.checkbox doesn't seem to handle centering very well. The following div compensates for that.
  div [style ["text-align"=>"left", "display"=>"inline-block", "width"=>"400px"]]
    [ Toggles.checkbox Mdl [index] model.mdl
        [ Options.onToggle msger
        , Toggles.value value
        ]
        [span [style ["font-size"=>"24pt", "margin-left"=>"16px"]] [ text label ]]
    ]

sceneValidationMsgs: List String -> Html Msg
sceneValidationMsgs msgs =
  if msgs == [] then text ""
  else
      div []
        (List.concat
          [ [ span [style ["font-size"=>"32pt"]] [text "Whoops!"], vspace 15 ]
          , List.map
              (\msg -> p [style ["color"=>"red", "font-size"=>"22pt"]] [text msg])
              msgs
          , [ span [] [text "Please correct these issues and try again."] ]
          ]
        )

vspace : Int -> Html Msg
vspace amount =
  div [style ["height" => (toString amount ++ "px")]] []

hspace : Int -> Html Msg
hspace amount =
  div [style ["display" => "inline-block", "width" => (toString amount ++ "px")]] []

-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

welcomeScene : Model -> Html Msg
welcomeScene model =
  genericSceneView model
    "Welcome!"
    "Is this your first visit?"
    (text "")
    [ ButtonSpec "First Visit" (PushScene HaveAcctQ)
    , ButtonSpec "Returning" (PushScene CheckIn)
    ]

-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

haveAcctScene : Model -> Html Msg
haveAcctScene model =
  genericSceneView model
    "Great!"
    "Do you already have an account here or on our website?"
    (text "")
    [ ButtonSpec "Yes" (PushScene CheckIn)
    , ButtonSpec "No" (PushScene LetsCreate)
    -- TODO: How about a "I don't know" button, here?
    ]

-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

checkInScene : Model -> Html Msg
checkInScene model =
  genericSceneView model
    "Let's Get You Checked-In!"
    "Who are you?"
    ( div []
        (List.concat
          [ [sceneTextField model 1 "Your Username or Surname" model.flexId UpdateFlexId, vspace 0]
          , if List.length model.matches > 0
             then [vspace 30, text "Tap your userid, below:", vspace 20]
             else [vspace 0]
          , List.map (\acct -> Chip.button [Options.onClick (LogCheckIn acct.memberNum)] [ Chip.content [] [ text acct.userName]]) model.matches
          ]
        )
    )
    []  -- No buttons

-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

letsCreateScene : Model -> Html Msg
letsCreateScene model =
  genericSceneView model
    "Let's Create an Account!"
    "Please tell us about yourself:"
    ( div []
        [ sceneTextField model 2 "Your first name" model.visitor.firstName UpdateFirstName
        , vspace 0
        , sceneTextField model 3 "Your last name" model.visitor.lastName UpdateLastName
        , vspace 0
        , sceneEmailField model 4 "Your email address" model.visitor.email UpdateEmail
        , vspace 30
        , sceneCheckbox model 5 "Check if you are 18 or older!" model.visitor.isAdult ToggleIsAdult
        ]
    )
    [ButtonSpec "OK" (PushScene ChooseUserNameAndPw)]

-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

chooseUserNameAndPwScene : Model -> Html Msg
chooseUserNameAndPwScene model =
  genericSceneView model
    "Account Details"
    "Provide an id and password for your account:"
    ( div []
        [ sceneTextField model 6 "Choose a user name" model.visitor.userName UpdateUserName
        , vspace 0
        , scenePasswordField model 7 "Choose a password" model.visitor.password UpdatePassword
        , vspace 0
        , scenePasswordField model 8 "Type password again" model.visitor.password2 UpdatePassword2
        , vspace 30
        , sceneValidationMsgs model.validationMessages
        ]
    )
    [ButtonSpec "OK" ValidateUserIdAndPw]

validateUserIdAndPw : Model -> (Model, Cmd Msg)
validateUserIdAndPw model =
  let
    pwMismatch = model.visitor.password /= model.visitor.password2
    pwShort = String.length model.visitor.password < 6
    userNameShort = String.length model.visitor.userName < 4
    msgs = List.concat
      [ if pwMismatch then ["The password fields don't match"] else []
      , if pwShort then ["The password must have at least 6 characters."] else []
      , if userNameShort then ["The user name must have at least 4 characters."] else []
      ]
  in
    if List.length msgs > 0
    then
      ({model | validationMessages = msgs}, Cmd.none)
    else
      let
        url = "/members/reception/matching-accts/"++model.visitor.userName++"/"
        request = Http.get url decodeMatchingAcctInfo
        cmd = Http.send ValidateUserNameUniqueness request
      in
        ({model | validationMessages = []}, cmd)

validateUserNameUniqueness: Model -> Result Http.Error MatchingAcctInfo -> (Model, Cmd Msg)
validateUserNameUniqueness model result =
  case result of
    Ok {target, matches} ->
      let
        matchingNames = List.map (\x -> String.toLower x.userName) matches
        chosenName = String.toLower model.visitor.userName
      in
        if List.member chosenName matchingNames then
          ({model | error = Nothing, validationMessages = ["That user name is already in use."]}, Cmd.none)
        else
          ({model | error = Nothing}, Cmd.none) :> update (PushScene HowDidYouHear)
    Err error ->
      ({model | error = Just (toString error)}, Cmd.none)

-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

howDidYouHearScene : Model -> Html Msg
howDidYouHearScene model =
  genericSceneView model
    "Just Wondering"
    "How did you hear about us?"
    (howDidYouHearChoices model)
    [ButtonSpec "OK" (PushScene Waiver)]

howDidYouHearChoices : Model -> Html Msg
howDidYouHearChoices model =
  Lists.ul howDidYouHearCss
    (List.map
      ( \dm ->
          Lists.li [css "font-size" "18pt"]
            [ Lists.content [] [ text dm.name ]
            , Lists.content2 []
              [ Toggles.checkbox Mdl [1000+dm.id] model.mdl  -- 1000 establishes an id range for these.
                  [ Toggles.value dm.selected
                  , Options.onToggle (ToggleDiscoveryMethod dm)
                  ]
                  []
              ]
            ]
      )
      model.discoveryMethods
    )

-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

waiverScene : Model -> Html Msg
waiverScene model =
  -- TODO: Don't present this to minors.
  -- TODO: Don't present this to people who have already signed.
  genericSceneView model
    ("Be Careful at " ++ model.orgName ++ "!")
    "Please read and sign the following waiver"
    (div []
      [ vspace 20
      , div [id "waiver-box", (waiverBoxStyle model.isSigning)]
          waiverHtml
      , div [style ["display"=>if model.isSigning then "block" else "none"]]
          [ p [style ["margin-top"=>"50px", "font-size"=>"16pt", "margin-bottom"=>"5px"]]
            [text "sign in box below:"]
          , canvas [width 760, height 200, id "signature-pad", signaturePadStyle] []
          ]
      ]
    )
    ( if model.isSigning then
        [ ButtonSpec "Accept" GetSignature
        , ButtonSpec "Clear" (ClearSignaturePad "signature-pad")
        ]
      else
        [ ButtonSpec "Sign" (ShowSignaturePad "signature-pad")
        ]
    )

-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

activityScene : Model -> Html Msg
activityScene model =
  genericSceneView model
    "Today's Activity"
    "Let us know what you'll be doing today"
    (makeActivityList model
      [ Curiousity
      , ClassParticipant
      , MemberPrivileges
      , GuestOfMember
      , Volunteer
      , Other
      ]
    )
    [ButtonSpec "OK" (PushScene Done)]

makeActivityList : Model -> List ReasonForVisit -> Html Msg
makeActivityList model reasons =
  Lists.ul activityListCss
    (List.indexedMap
      ( \index reason ->
          Lists.li [css "font-size" "18pt"]
            [ Lists.content [] [text (reasonString model reason)]
            , Lists.content2 []
              [ Toggles.radio Mdl [2000+index] model.mdl  -- 1000 establishes an id range for these.
                  [ Toggles.value
                      ( case model.reasonForVisit of
                        Nothing -> False
                        Just r -> r == reason
                      )
                  , Options.onToggle (UpdateReasonForVisit reason)
                  ]
                  []
              ]
            ]
      )
      reasons
    )

-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

doneScene : Model -> Html Msg
doneScene model =
  genericSceneView model
    "You're Checked In"
    "Have fun!"
    (text "")
    [ButtonSpec "Yay!" (PushScene Welcome)]


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------

subscriptions: Model -> Sub Msg
subscriptions model =
  Sub.batch
    [
        signatureImage UpdateSignature
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

decodeDiscoveryMethod : Dec.Decoder DiscoveryMethod
decodeDiscoveryMethod =
  decode DiscoveryMethod
    |> required "id" Dec.int
    |> required "name" Dec.string
    |> required "order" Dec.int
    |> hardcoded False

decodeDiscoveryMethodInfo : Dec.Decoder DiscoveryMethodInfo
decodeDiscoveryMethodInfo =
  Dec.map4 DiscoveryMethodInfo
    (Dec.field "count" Dec.int)
    (Dec.field "next" (Dec.maybe Dec.string))
    (Dec.field "previous" (Dec.maybe Dec.string))
    (Dec.field "results" (Dec.list decodeDiscoveryMethod))


-----------------------------------------------------------------------------
-- Should be in external HTML files
-----------------------------------------------------------------------------

waiverHtml : List (Html Msg)
waiverHtml =
  [ p [style ["font-size"=>"20pt", "font-weight"=>"bold", "margin-top"=>"10px"]]
      [ text "XEROCRAFT INC. RELEASE AND WAIVER OF LIABILITY, ASSUMPTION OF RISK, AND INDEMNITY CONSENT AGREEMENT"
      , br [] []
      , text "('Agreement')"
      ]
  , div [style ["text-align"=>"left", "margin-top"=>"20px"]]
      [ p [style ["font-size"=>"16pt", "line-height"=>"15pt"]] [ text "IN CONSIDERATION of being permitted to participate in any way in the activities of Xerocraft Inc. I, for myself or personal representatives, assigns, heirs, and next of kin:" ]
      , ol [style ["font-size"=>"16pt", "line-height"=>"15pt"]]
          [ li [style ["margin-bottom"=>"15px"]] [text "ACKNOWLEDGE, agree, and represent that I understand the nature of Xerocraft inc.'s activities and that I am sober, qualified, in good health, and in proper physical and mental condition to participate in such Activity. I further agree and warrant that if at any time I believe conditions to be unsafe, I will immediately discontinue further participation in the Activity." ]
          , li [style ["margin-bottom"=>"15px"]]
              [ text "FULLY UNDERSTAND THAT: (a) "
              , b [] [text "THESE ACTIVITIES MAY INVOLVE RISKS AND DANGERS OF SERIOUS BODILY INJURY, INCLUDING PERMANENT DISABILITY, AND DEATH " ]
              , text "('RISKS'); (b) these Risks and dangers may be caused by my own actions or inaction's, the actions or inaction's of others participating in the Activity, the condition(s) under which the Activity takes place, or THE NEGLIGENCE OF THE 'RELEASEES' NAMED BELOW; (c) there may be OTHER RISK AND SOCIAL AND ECONOMIC LOSSES either not known to me or not readily foreseeable at this time; and I FULLY ACCEPT AND ASSUME ALL SUCH RISKS AND ALL RESPONSIBILITY FOR LOSSES, COSTS, AND DAMAGES I incur as a result of my participation or that of the minor in the Activity."
              ]
          , li [] [text "HEREBY RELEASE, DISCHARGE, AND COVENANT NOT TO SUE Xerocraft inc., their respective administrators, directors, agents, officers, members, volunteers, and employees, other participants, any sponsors, advertisers, and, if applicable, owner(s) and lessors of premises on which the Activity takes place, (each considered one of the 'RELEASEES' herein) FROM ALL LIABILITY, CLAIMS, DEMANDS, LOSSES, OR DAMAGES ON OR BY MY ACCOUNT CAUSED OR ALLEGED TO BE CAUSED IN WHOLE OR IN PART BY THE NEGLIGENCE OF THE 'RELEASEES' OR OTHERWISE, INCLUDING NEGLIGENT RESCUE OPERATIONS AND I FURTHER AGREE that if, despite this RELEASE AND WAIVER OF LIABILITY, ASSUMPTION OF RISK, AND INDEMNITY AGREEMENT I, or anyone on my behalf, makes a claim against any of the Releasees, I WILL INDEMNIFY, SAVE, AND HOLD HARMLESS EACH OF THE RELEASEES from any litigation expenses, attorney fees, loss, liability, damage, or cost which may incur as the result of such claim. I have read this Agreement, fully understand its terms, understand that I have given up substantial rights by signing it and have signed it freely and without inducement or assurance of any nature and intend it to be a complete and unconditional release of all liability to the greatest extent allowed by law and agree that if any portion of this Agreement is held to be invalid the balance, notwithstanding, shall continue in full force and effect." ]
          ]
      , p [style ["font-size"=>"16pt", "line-height"=>"15pt"]]
          [ b [] [text "MINOR RELEASE."]
          , text "The minor's parent and/or legal guardian, understand the nature of Xerocraft inc.'s activities and the minor's experience and capabilities and believe the minor to be qualified, in good health, and in proper physical and mental condition to participate in such activity. I hereby release, discharge, covenant not to sue, and agree to indemnify and save and hold harmless each of the releasee's from all liability claims, demands, losses, or damages on the minor's account caused or alleged to be caused in whole or in part by the negligence of the 'releasees' or otherwise, including negligent rescue operation and further agree that if, despite this release, I, the minor, or anyone on the minor's behalf makes a claim against any of the releasees named above, I will indemnify, save, and hold harmless each of the releasees from any litigation expenses, attorney fees, loss liability, damage, or any cost which may incur as the result of any such claim."
          ]
      ]
  ]


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

(=>) = (,)

px : Int -> String
px num = (toString num) ++ "px"

-- The reception kiosk is being designed to run full-screen on Motorola Xooms.
-- These have resolution 1280 x 800 at about 150ppi.
-- When testing on desktop, the scene should be about 13.6cm wide.

sceneWidth = 800
sceneHeight = 1280
topBannerHeight = 155
bottomBannerHeight = 84

canvasDivStyle = style
  [ "font-family" => "Roboto Condensed, Arial, Helvetica"
  , "text-align" => "center"
  , "padding-left" => "0"
  , "padding-right" => "0"
  , "padding-top" => px topBannerHeight
  , "padding-bottom" => px bottomBannerHeight
  , "position" => "absolute"
  , "top" => "0"
  , "bottom" => "0"
  , "left" => "0"
  , "right" => "0"
  ]

sceneDivBorderWidth = 1
sceneDivStyle = style
  [ "margin-left" => "auto"
  , "margin-right" => "auto"
  , "border" => "1px solid #bbbbbb"
  , "background-color" => "white"
  , "width" => px (sceneWidth - 2*sceneDivBorderWidth)
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
  , "margin-top" => px (-1*topBannerHeight)
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "height" => px topBannerHeight
  , "width" => px sceneWidth
  ]

bannerBottomStyle = style
  [ "display" => "block"
  , "margin-bottom" => px (-1*bottomBannerHeight)
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "height" => px bottomBannerHeight
  , "width" => px sceneWidth
  ]

navDivStyle = bannerBottomStyle

waiverBoxStyle isSigning = style
  [ "height" => if isSigning then "300px" else "600px"
  , "overflow-y" => "scroll"
  , "margin-left" => "20px"
  , "margin-right" => "20px"
  , "border" => "1px solid #bbbbbb"
  , "font-size" => "16pt"
  , "padding" => "5px"
  ]

signaturePadStyle = style
  [ "height" => "200px"
  , "width" => "760px"
  , "border" => "1px solid #bbbbbb"
  , "cursor" => "crosshair"
  , "touch-action" => "none"
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

navButtonCss =
  [ css "display" "inline-block"
  , css "margin-top" "30px"
  , css "font-size" "14pt"
  , css "color" "#eeeeee"
  ]

sceneChipCss =
  [ css "margin-left" "3px"
  , css "margin-right" "3px"
  ]

howDidYouHearCss =
  [ css "width" "400px"
  , css "margin-left" "auto"
  , css "margin-right" "auto"
  , css "margin-top" "80px"
  ]

activityListCss =
  [ css "width" "450px"
  , css "margin-left" "auto"
  , css "margin-right" "auto"
  , css "margin-top" "80px"
  ]