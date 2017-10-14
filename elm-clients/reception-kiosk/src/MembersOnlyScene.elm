
module MembersOnlyScene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , MembersOnlyModel
  , getTimeBlocks  -- For ScreenSaver
  )

-- Standard
import Html exposing (..)
import Html.Attributes exposing (..)
import Regex exposing (regex)
import Time exposing (Time)
import Date exposing (Date)

-- Third Party
import String.Extra exposing (..)
import Date.Extra as DateX

-- Local
import MembersApi as MembersApi exposing (Membership)
import XerocraftApi as XcApi
import OpsApi as OpsApi exposing (TimeBlock, TimeBlockType)
import Wizard.SceneUtils exposing (..)
import CheckInScene exposing (CheckInModel)
import Types exposing (..)
import Fetchable exposing (..)


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type PaymentInfoState
  = AskingIfMshipCurrent
  | ConfirmingPaymentInfoSent
  | ExplainingHowToPayNow

type alias MembersOnlyModel =
  { nowBlock : Fetchable (Maybe TimeBlock)
  , allTypes : Fetchable (List TimeBlockType)
  , memberships : Fetchable (List Membership)
  , paymentInfoState : PaymentInfoState
  , badNews : List String
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  (SceneUtilModel
    { a
    | membersOnlyModel : MembersOnlyModel
    , checkInModel : CheckInModel
    , currTime : Time
    , flags : Flags
    }
  )

init : Flags -> (MembersOnlyModel, Cmd Msg)
init flags =
  let sceneModel =
    { nowBlock = Pending
    , allTypes = Pending
    , memberships = Pending
    , paymentInfoState = AskingIfMshipCurrent
    , badNews = []
    }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (MembersOnlyModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  let sceneModel = kioskModel.membersOnlyModel
  in case appearingScene of

    ReasonForVisit ->
      -- We want to have the current time block on hand by the time MembersOnly
      -- appears, so start the fetch when ReasonForVisit appears.
      let
        memberNum = kioskModel.checkInModel.memberNum
        cmd1 = getTimeBlocks kioskModel.flags
        cmd2 = getMemberships kioskModel memberNum
        cmd3 = getTimeBlockTypes kioskModel
        cmds = Cmd.batch [cmd1, cmd2, cmd3]
      in
        (sceneModel, cmds)

    MembersOnly ->
      if haveSomethingToSay kioskModel
        then (sceneModel, Cmd.none)  -- NO-OP. We will show this scene.
        else (sceneModel, segueTo CheckInDone)  -- Will skip this scene.

    _ ->
      (sceneModel, Cmd.none)  -- Ignore all other scene appearances.


{- Will keep this simple, for now. This scene will appear if all of the following are true:
   (1) We know what type of time block we're in.
   (2) The time block is tagged as being for Supporting Members Only.
   (3) We have the user's membership info.
-}
haveSomethingToSay : KioskModel a -> Bool
haveSomethingToSay kioskModel =
  let
    sceneModel = kioskModel.membersOnlyModel
    membersOnlyStr = "Members Only"
  in
    case (sceneModel.nowBlock, sceneModel.allTypes, sceneModel.memberships) of

      -- Following is the case where somebody arrives during an explicit time block.
      (Received (Just nowBlock), Received allTypes, Received memberships) ->
        let
          nowBlockTypes = OpsApi.blocksTypes nowBlock allTypes
          isMembersOnly = List.member membersOnlyStr (List.map .name nowBlockTypes)
          membershipIsCurrent = MembersApi.coverNow memberships kioskModel.currTime
        in
          isMembersOnly && not membershipIsCurrent

      -- Following is the case where we're not in any explicit time block.
      -- So use default time block type, if one has been specified.
      (Received Nothing, Received allTypes, Received memberships) ->
        let
          defaultBlockType = OpsApi.defaultType allTypes
          isMembersOnly =
            case defaultBlockType of
              Just bt -> bt.name == membersOnlyStr
              Nothing -> False
          current = MembersApi.coverNow memberships kioskModel.currTime
        in
          isMembersOnly && not current

      _ -> False


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : MembersOnlyMsg -> KioskModel a -> (MembersOnlyModel, Cmd Msg)
update msg kioskModel =

  let
    sceneModel = kioskModel.membersOnlyModel

  in case msg of

    -- SUCCESSFUL FETCHES --

    UpdateTimeBlocks (Ok pageOfTimeBlocks) ->
      let
        blocks = pageOfTimeBlocks.results
        nowBlocks = List.filter .isNow blocks
        nowBlock = List.head nowBlocks
      in
        ({sceneModel | nowBlock = Received nowBlock }, Cmd.none)

    UpdateTimeBlockTypes (Ok pageOfTimeBlockTypes) ->
      ({sceneModel | allTypes = Received pageOfTimeBlockTypes.results}, Cmd.none)

    UpdateMemberships (Ok pageOfMemberships) ->
      let memberships = pageOfMemberships.results
      in ({sceneModel | memberships = Received memberships}, Cmd.none)


    -- FAILED FETCHES --

    UpdateTimeBlocks (Err error) ->
      let msg = toString error |> Debug.log "Error getting time blocks: "
      in ({sceneModel | nowBlock = Failed msg}, Cmd.none)

    UpdateTimeBlockTypes (Err error) ->
      let msg = toString error |> Debug.log "Error getting time block types: "
      in ({sceneModel | allTypes = Failed msg}, Cmd.none)

    UpdateMemberships (Err error) ->
      let msg = toString error |> Debug.log "Error getting memberships: "
      in ({sceneModel | memberships = Failed msg}, Cmd.none)

    -- PAYMENT ACTIONS --

    SendPaymentInfo ->
      ({sceneModel | paymentInfoState = ConfirmingPaymentInfoSent}, Cmd.none)

    PayNowAtFrontDesk ->
      ({sceneModel | paymentInfoState = ExplainingHowToPayNow}, Cmd.none)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.membersOnlyModel
  in
    genericScene kioskModel
      "Supporting Members Only"
      "Is your supporting membership up to date?"
      (
      case sceneModel.paymentInfoState of
        AskingIfMshipCurrent -> areYouCurrentContent kioskModel
        ConfirmingPaymentInfoSent -> paymentInfoSentContent kioskModel
        ExplainingHowToPayNow -> howToPayNowContent kioskModel
      )
      []  -- No buttons here. They will be woven into content.
      []  -- No bad news. Scene will fail silently, but should log somewhere.

areYouCurrentContent : KioskModel a -> Html Msg
areYouCurrentContent kioskModel =
  let
    sceneModel = kioskModel.membersOnlyModel
  in
    case sceneModel.memberships of

      Received memberships ->
        let
          however = "However, you may have made a more recent payment that we haven't yet processed."
          mostRecent = MembersApi.mostRecentMembership memberships
          paymentMsg = case mostRecent of
            Just mship ->
              "Our records show that your most recent membership has an expiration date of "
              ++ DateX.toFormattedString "dd-MMM-yyyy" mship.endDate
              ++ ". "
            Nothing ->
              "We have no record of previous payments by you. "
        in
          div [sceneTextStyle, sceneTextBlockStyle]
              [ vspace 20
              , text (paymentMsg ++ however)
              , vspace 40
              , text "If it's time to renew your membership,"
              , vspace 0
              , text "choose one of the following:"
              , vspace 20
                -- TODO: Should display other options for Work Traders.
                -- TODO: Payment options should come from a single source on the backend.
              , sceneButton kioskModel (ButtonSpec "Send Me Payment Info" (MembersOnlyVector <| SendPaymentInfo))
              , vspace 20
              , sceneButton kioskModel (ButtonSpec "Pay Now at Front Desk" (MembersOnlyVector <| PayNowAtFrontDesk))
                -- TODO: If visitor is a keyholder, offer them 1day for $10
              , vspace 40
              , text "If your membership is current, thanks!"
              , vspace 0
              , text "Just click below."
              , vspace 20
              , sceneButton kioskModel (ButtonSpec "I'm Current!" (WizardVector <| Push <| CheckInDone))
              ]

      _ ->
        let
          errMsg = "ERROR: We shouldn't get to view func if memberships haven't been received"
        in
          text errMsg

paymentInfoSentContent : KioskModel a -> Html Msg
paymentInfoSentContent kioskModel =
  let
    sceneModel = kioskModel.membersOnlyModel
  in
    div [sceneTextStyle, sceneTextBlockStyle]
      [ vspace 80
      , img [src "/static/bzw_ops/EmailSent.png", emailSentImgStyle] []
      , vspace 20
      , text "We've sent payment information to you via email!"
      , vspace 0
      , text "Please be sure to renew before visiting another"
      , vspace 0
      , text "\"Supporting Members Only\" session."
      , vspace 40
      , sceneButton kioskModel (ButtonSpec "OK" (WizardVector <| Push <| CheckInDone))
      ]

howToPayNowContent : KioskModel a -> Html Msg
howToPayNowContent kioskModel =
  let
    sceneModel = kioskModel.membersOnlyModel
  in
    div [sceneTextStyle, sceneTextBlockStyle]
      [ vspace 60
      , img [src "/static/bzw_ops/VisaMcDiscAmexCashCheck.png", payTypesImgStyle] []
      , vspace 40
      , text "We accept credit card, cash, and checks."
      , vspace 0
      , text "Please ask a Staffer for assistance."
      , vspace 0
      , text "Thanks!"
      , vspace 60
      , sceneButton kioskModel (ButtonSpec "OK" (WizardVector <| Push <| CheckInDone))
      ]


-----------------------------------------------------------------------------
-- COMMANDS
-----------------------------------------------------------------------------

getTimeBlocks : Flags -> Cmd Msg
getTimeBlocks flags =
  OpsApi.getTimeBlocks flags (MembersOnlyVector << UpdateTimeBlocks)

getTimeBlockTypes : KioskModel a  -> Cmd Msg
getTimeBlockTypes kioskModel =
  OpsApi.getTimeBlockTypes
    kioskModel.flags
    (MembersOnlyVector << UpdateTimeBlockTypes)

getMemberships : KioskModel a -> Int -> Cmd Msg
getMemberships kioskModel memberNum =
  MembersApi.getMemberships
    kioskModel.flags
    memberNum
    (MembersOnlyVector << UpdateMemberships)


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

emailSentImgStyle = style
  [ "text-align" => "center"
  , "width" => px 200
  , "margin-left" => px -80
  ]

payTypesImgStyle = style
  [ "text-align" => "center"
  , "width" => px 400
  ]
