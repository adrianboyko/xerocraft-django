
module CreatingAcctScene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , tick
  , CreatingAcctModel
  )

-- Standard
import Html exposing (..)
import Html.Attributes exposing (..)
import Regex exposing (regex)
import Time exposing (Time)

-- Third Party
import String.Extra exposing (..)
import List.Nonempty exposing (Nonempty)
import Material

-- Local
import MembersApi as MembersApi
import XerocraftApi as XcApi
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import ReasonForVisitScene exposing (ReasonForVisitModel)
import NewMemberScene exposing (NewMemberModel)
import NewUserScene exposing (NewUserModel)
import WaiverScene exposing (WaiverModel)
import HowDidYouHearScene exposing (HowDidYouHearModel)

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
  , creatingAcctModel : CreatingAcctModel
  , membersApi : MembersApi.Session Msg
  }


type alias CreatingAcctModel =
  ------------ REQ'D ARGS:
  { methods : Maybe (List Int)
  , firstName : Maybe String
  , lastName : Maybe String
  , email : Maybe String
  , isAdult : Maybe Bool
  , userName : Maybe String
  , password : Maybe String
  , signature : Maybe String
  ------------ OTHER STATE:
  , waitCount : Int
  , badNews : List String
  }

init : Flags -> (CreatingAcctModel, Cmd Msg)
init flags =
  let sceneModel =
    ------------------ We start with no args:
    { methods = Nothing
    , firstName = Nothing
    , lastName = Nothing
    , email = Nothing
    , isAdult = Nothing
    , userName = Nothing
    , password = Nothing
    , signature = Nothing
    ---------------------- Other state:
    , waitCount = 0
    , badNews = []
    }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- ARG HELPERS
-----------------------------------------------------------------------------

-- Pulls the arguments from the rest of the model.
args m =
  ( m.methods
  , m.firstName
  , m.lastName
  , m.email
  , m.isAdult
  , m.userName
  , m.password
  , m.signature
  )


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (CreatingAcctModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  let
    sceneModel = kioskModel.creatingAcctModel
  in
    if appearingScene == CreatingAcct then
      case args sceneModel of
        (Just _, Just fname, Just lname, Just email, Just _, Just uname, Just pw, Just sig) ->
          let
            fullName = String.join " " [fname, lname]
            cmd = kioskModel.membersApi.createNewAcct
              fullName uname email pw sig
              (CreatingAcctVector << XcAcctCreationAttempted)
          in
            (sceneModel, cmd)

        (_, _, _, _, _, _, _, _) ->
          (sceneModel, send <| ErrorVector <| ERR_Segue missingArguments)

    else
      (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : CreatingAcctMsg -> KioskModel a -> (CreatingAcctModel, Cmd Msg)
update msg kioskModel =

  let
    sceneModel = kioskModel.creatingAcctModel

  in case msg of

    CA_Segue (methods, fname, lname, email, adult, uname, pw, sig) ->

      ( { sceneModel
        | methods = Just methods
        , firstName = Just fname
        , lastName = Just lname
        , email = Just email
        , isAdult = Just adult
        , userName = Just uname
        , password = Just pw
        , signature = Just sig
        }
      , send <| WizardVector <| Push <| CreatingAcct
      )

    XcAcctCreationAttempted (Ok htmlResponseBody) ->
      let
        successIndicator = "<h1>You have successfully registered your check in! Welcome to Xerocraft!</h1>"
        userNameInUseIndicator = "<h2></h2>"
        -- Seems to present errors in div#Message.
        -- E.g. <div id="Message"><h2>This username is already being used.</h2></div>
        msgRegex = regex "<div id=\\\"Message\\\">.*</div>"
        tagRegex = regex "<[^>]*>"
        msgsFound = Regex.find (Regex.AtMost 1) msgRegex htmlResponseBody
        msg = case List.head msgsFound of
          Nothing -> ""
          Just m -> stripTags m.match
      in
        case msg of

          "You have successfully registered your check in! Welcome to Xerocraft!" ->
            -- This is the result we wanted. Account creation was successful.
            let
              flags = kioskModel.flags
              cloneFn = XcApi.cloneAcctToXis flags.cloneAcctUrl flags.csrfToken
              resultToMsg = CreatingAcctVector << CloneAttempted
            in
              case args sceneModel of
                (Just _, Just _, Just _, Just _, Just _, Just uname, Just pw, Just _) ->
                  ({sceneModel | badNews=[]}, cloneFn uname pw resultToMsg)
                _ ->
                  (sceneModel, send <| ErrorVector <| ERR_Segue missingArguments)

          "" ->
            -- Couldn't find a message so dump the entire response body as a debugging aid.
            -- We don't expect this to happen.
            ({sceneModel | badNews = [stripTags htmlResponseBody]}, Cmd.none)

          _ ->
            -- All other messages are treated as errors and reported as such to user.
            -- Many of the possible errors are validation related so we shouldn't see them if
            -- the client-side validation in earlier scenes was effective.
            ({sceneModel | badNews = [msg]}, Cmd.none)

    XcAcctCreationAttempted (Err error) ->
      -- This is genuinely bad news as creating this acct is the main point of sign up.
      ({sceneModel | badNews = ["Could not create acct on xerocraft.org", toString error]}, Cmd.none)

    CloneAttempted (Err error) ->
      -- It's not critically important that this succeeds.
      -- Worst case scenario is that new account will be cloned by the acct scraper, that night.
      -- TODO: log/report error somewhere. ["Acct created but not cloned.", toString error]
      ({sceneModel | badNews = []}, infoToXisAcct kioskModel)

    CloneAttempted (Ok responseStr) ->
      -- The clone to XIS has succeeded so we can now push info that XIS wants.
      ({sceneModel | badNews = []}, infoToXisAcct kioskModel)

    IsAdultWasSet (Ok ignored) ->
      -- User has moved on while this ran in the background. No action required on success.
      (sceneModel, Cmd.none)

    IsAdultWasSet (Err error) ->
      -- It's not critically important that this succeeds. Hundreds of existing accts don't have adult/minor info.
      -- TODO: log/report error somewhere. ["Setting isAdult failed.", toString error]
      (sceneModel, Cmd.none)

    DiscoveryMethodAdded (Ok ignored) ->
      -- User has moved on while this ran in the background. No action required on success.
      (sceneModel, Cmd.none)

    DiscoveryMethodAdded (Err error) ->
      -- It's not critically important that this succeeds.
      -- TODO: log/report error somewhere. ["Adding discovery method failed.", toString error]
      (sceneModel, Cmd.none)


infoToXisAcct : KioskModel a -> Cmd Msg
infoToXisAcct kioskModel =
  case args kioskModel.creatingAcctModel of
    (Just methods, Just _, Just _, Just _, Just adult, Just uname, Just pw, Just _) ->
      let
        sceneModel = kioskModel.creatingAcctModel
        membersApi = kioskModel.membersApi
        -- TODO?: Change setIsAdult to setMemberInfo and also pass fname, lname, and email.
        setIsAdultCmd =
          membersApi.setIsAdult uname pw adult
          (CreatingAcctVector << IsAdultWasSet)
        addMethodsCmd =
          membersApi.addDiscoveryMethods uname pw  methods
          (CreatingAcctVector << DiscoveryMethodAdded)
        segueCmd = send <| SignUpDoneVector <| SUD_Segue uname
      in
        Cmd.batch [segueCmd, setIsAdultCmd, addMethodsCmd]
    _ ->
      send <| ErrorVector <| ERR_Segue missingArguments


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  -- TODO: Don't present this to minors.
  -- TODO: Don't present this to people who have already signed.
  let
    sceneModel = kioskModel.creatingAcctModel
  in
    genericScene kioskModel
      "Creating Your Account!"
      "One moment please"
      (div []
        (if List.isEmpty sceneModel.badNews then
            [ vspace 40
            , text "Working"
            , vspace 20
            , text (String.repeat sceneModel.waitCount "●")
            ]
        else
            [ vspace 40
            ]
        )
      )
      []  -- No buttons. Scene will automatically transition.
      sceneModel.badNews

-----------------------------------------------------------------------------
-- TICK (called each second)
-----------------------------------------------------------------------------

tick : Time -> KioskModel a -> (CreatingAcctModel, Cmd Msg)
tick time kioskModel =
  let
    visible = sceneIsVisible kioskModel CreatingAcct
    sceneModel = kioskModel.creatingAcctModel
    inc = if visible && List.isEmpty sceneModel.badNews then 1 else 0
    newWaitCount = sceneModel.waitCount + inc
  in
    if visible then ({sceneModel | waitCount=newWaitCount}, Cmd.none)
    else (sceneModel, Cmd.none)
