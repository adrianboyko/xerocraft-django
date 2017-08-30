
module ReceptionKiosk.CreatingAcctScene exposing (init, update, view, tick, CreatingAcctModel)

-- Standard
import Html exposing (..)
import Html.Attributes exposing (..)
import Regex exposing (regex)
import Time exposing (Time)

-- Third Party
import String.Extra exposing (..)

-- Local
import MembersApi as MembersApi
import XerocraftApi as XcApi
import ReceptionKiosk.Types exposing (..)
import ReceptionKiosk.SceneUtils exposing (..)
import ReceptionKiosk.ReasonForVisitScene exposing (ReasonForVisitModel)
import ReceptionKiosk.NewMemberScene exposing (NewMemberModel)
import ReceptionKiosk.NewUserScene exposing (NewUserModel)
import ReceptionKiosk.WaiverScene exposing (WaiverModel)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias CreatingAcctModel =
  { waitingForScrape : Bool
  , checkCount: Int
  , badNews : List String
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  (SceneUtilModel
    { a
    | creatingAcctModel : CreatingAcctModel
    , newMemberModel : NewMemberModel
    , newUserModel: NewUserModel
    , reasonForVisitModel: ReasonForVisitModel
    , waiverModel : WaiverModel
    }
  )

init : Flags -> (CreatingAcctModel, Cmd Msg)
init flags =
  let sceneModel =
    { waitingForScrape = False
    , checkCount = 0
    , badNews = []
    }
  in (sceneModel, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : CreatingAcctMsg -> KioskModel a -> (CreatingAcctModel, Cmd Msg)
update msg kioskModel =

  let sceneModel = kioskModel.creatingAcctModel
  in case msg of

    CreatingAcctSceneWillAppear ->
      let
        memberModel = kioskModel.newMemberModel
        userModel = kioskModel.newUserModel
        waiverModel = kioskModel.waiverModel
        fullName = String.join " " [memberModel.firstName, memberModel.lastName]
        cmd = MembersApi.createNewAcct
          fullName userModel.userName memberModel.email userModel.password1 waiverModel.signature
          (CreatingAcctVector << XcAcctCreationAttempted)
      in
        (sceneModel, cmd)

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
            -- Rebase the scene stack since we don't want the user backtracking into acct creation again.
            let
              newModel = {sceneModel | badNews=[]}
              scrapeLogins = XcApi.scrapeXcOrgLogins kioskModel.flags.scrapeLoginsUrl
              cmd = scrapeLogins (CreatingAcctVector << XcScrapeStarted)
            in
              (newModel, cmd)

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
      -- These will be http errors.
      ({sceneModel | badNews = [toString error]}, Cmd.none)

    XcScrapeStarted (Ok ignored) ->
      ({sceneModel | waitingForScrape=True}, Cmd.none)

    XcScrapeStarted (Err error) ->
      -- These will be http errors.
      ({sceneModel | badNews=[toString error], waitingForScrape=False}, Cmd.none)

    CheckedForAcct (Ok {target, matches}) ->
      if List.isEmpty matches then
        -- Nothing yet. Will try again on next Tick message.
      ({sceneModel | waitingForScrape=True}, Cmd.none)
      else
        let
          model = {sceneModel | waitingForScrape=False }
          cmd = send (WizardVector <| RebaseTo <| SignUpDone)
        in
          (model, cmd)

    CheckedForAcct (Err error) ->
      -- These will be http errors.
      ({sceneModel | badNews=[toString error], waitingForScrape=False}, Cmd.none)

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
            , text (String.repeat sceneModel.checkCount "●")
            ]
        else
            [ vspace 40
            , formatBadNews sceneModel.badNews
            ]
        )
      )
      []  -- No buttons. Scene will automatically transition.

-----------------------------------------------------------------------------
-- TICK (called each second)
-----------------------------------------------------------------------------

tick : Time -> KioskModel a -> (CreatingAcctModel, Cmd Msg)
tick time kioskModel =
  let
    sceneModel = kioskModel.creatingAcctModel
  in
    if sceneModel.waitingForScrape then
      checkForScrapedAcct kioskModel
    else
      (sceneModel, Cmd.none)

-- There are ways to drive this aside from ticks, so I've kept it as a separate function.
checkForScrapedAcct : KioskModel a -> (CreatingAcctModel, Cmd Msg)
checkForScrapedAcct kioskModel =
    let
      sceneModel = kioskModel.creatingAcctModel
      newCheckCount = sceneModel.checkCount + 1
      userId = kioskModel.newUserModel.userName
      getMatchingAccts = MembersApi.getMatchingAccts kioskModel.flags
      checkCmd = getMatchingAccts userId (CreatingAcctVector << CheckedForAcct)
      timeoutMsg = "Timeout waiting for new acct to migrate to XIS."
    in
      if newCheckCount > 20 then
        ({sceneModel | badNews=[timeoutMsg], waitingForScrape=False}, Cmd.none)
      else
        ({sceneModel | badNews=[], checkCount=newCheckCount, waitingForScrape=True}, checkCmd)
