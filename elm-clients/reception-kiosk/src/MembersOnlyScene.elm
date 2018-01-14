
module MembersOnlyScene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , MembersOnlyModel
  )

-- Standard
import Html exposing (..)
import Html.Attributes exposing (..)
import Regex exposing (regex)
import Time exposing (Time)
import Date exposing (Date)

-- Third Party
import String.Extra exposing (..)

-- Local
import XerocraftApi as XcApi
import XisRestApi as XisApi exposing (..)
import Wizard.SceneUtils exposing (..)
import CheckInScene exposing (CheckInModel)
import Types exposing (..)
import Fetchable exposing (..)
import CalendarDate


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  (SceneUtilModel
    { a
    | membersOnlyModel : MembersOnlyModel
    , checkInModel : CheckInModel
    , currTime : Time
    , flags : Flags
    , xisSession : XisApi.Session Msg
    }
  )


type PaymentInfoState
  = AskingIfMshipCurrent
  | ConfirmingPaymentInfoSent
  | ExplainingHowToPayNow


type alias MembersOnlyModel =
  { nowBlock : Fetchable (Maybe TimeBlock)
  , allTypes : Fetchable (List TimeBlockType)
  , paymentInfoState : PaymentInfoState
  , badNews : List String
  }


init : Flags -> (MembersOnlyModel, Cmd Msg)
init flags =
  let sceneModel =
    { nowBlock = Pending
    , allTypes = Pending
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
        xis = kioskModel.xisSession
        cmd1 = xis.listTimeBlocks (MembersOnlyVector << UpdateTimeBlocks)
        cmd2 = xis.listTimeBlockTypes (MembersOnlyVector << UpdateTimeBlockTypes)
      in
        (sceneModel, Cmd.batch [cmd1, cmd2])

    MembersOnly ->
      if (haveSomethingToSay kioskModel |> Debug.log "Something To Say: ")
        then (sceneModel, Cmd.none)  -- We need to talk, so show this scene.
        else (sceneModel, segueTo OldBusiness)  -- Nothing to say, so skip this scene.

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
    mship = kioskModel.checkInModel.checkedInMember
      |> Maybe.andThen (.data >> .latestNonfutureMembership)
    membersOnlyStr = "Members Only"
    xis = kioskModel.xisSession
  in
    case (sceneModel.nowBlock, sceneModel.allTypes, mship) of

      -- Following is the case where somebody arrives during an explicit time block.
      (Received (Just nowBlock), Received allTypes, Just mship) ->
        let
          nowBlockTypes = kioskModel.xisSession.getBlocksTypes nowBlock allTypes
          isMembersOnly = List.member membersOnlyStr (List.map (.data >> .name) nowBlockTypes)
          membershipIsCurrent = xis.coverTime [mship] kioskModel.currTime
        in
          isMembersOnly && not membershipIsCurrent

      -- Following is the case where we're not in any explicit time block.
      -- So use default time block type, if one has been specified.
      (Received Nothing, Received allTypes, Just mship) ->
        let
          defaultBlockType = xis.defaultBlockType allTypes
          isMembersOnly =
            case defaultBlockType of
              Just bt -> bt.data.name == membersOnlyStr
              Nothing -> False
          current = xis.coverTime [mship] kioskModel.currTime
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

    UpdateTimeBlocks (Ok {results}) ->
      let
        nowBlocks = List.filter (.data >> .isNow) results
        nowBlock = List.head nowBlocks
      in
        ({sceneModel | nowBlock = Received nowBlock }, Cmd.none)

    UpdateTimeBlockTypes (Ok {results}) ->
      ({sceneModel | allTypes = Received results}, Cmd.none)


    -- FAILED FETCHES --

    UpdateTimeBlocks (Err error) ->
      let msg = toString error |> Debug.log "Error getting time blocks: "
      in ({sceneModel | nowBlock = Failed msg}, Cmd.none)

    UpdateTimeBlockTypes (Err error) ->
      let msg = toString error |> Debug.log "Error getting time block types: "
      in ({sceneModel | allTypes = Failed msg}, Cmd.none)


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
    xis = kioskModel.xisSession
  in
    case kioskModel.checkInModel.checkedInMember of

      Nothing ->
        -- We shouldn't be able to get to this scene without a defined checkedInMember.
        -- If it happens, we'll log a message and display an error message.
        let _ = Debug.log "checkedInMember" Nothing
        in text "ERROR: checkedInMember not specified"

      Just checkedInMember ->
        let
          however = "However, you may have made a more recent payment that we haven't yet processed."
          paymentMsg = case checkedInMember.data.latestNonfutureMembership of
            Just mship ->
              "Our records show that your most recent membership has an expiration date of "
              ++ CalendarDate.format "%d-%b-%Y" mship.data.endDate
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
              , sceneButton kioskModel <| ButtonSpec "I'm Current!" (msgForSegueTo OldBusiness)
              ]


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
      , sceneButton kioskModel <| ButtonSpec "OK" (msgForSegueTo OldBusiness)
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
      , sceneButton kioskModel <| ButtonSpec "OK" (msgForSegueTo OldBusiness)
      ]


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
