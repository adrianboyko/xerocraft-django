
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
import Material
import List.Nonempty exposing (Nonempty)

-- Local
import XerocraftApi as XcApi
import XisRestApi as XisApi exposing (..)
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import CalendarDate


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
  , membersOnlyModel : MembersOnlyModel
  , currTime : Time
  , xisSession : XisApi.Session Msg
  }


type PaymentInfoState
  = AskingIfMshipCurrent
  | SendingPaymentInfo
  | PaymentInfoSent
  | ExplainingHowToPayNow


type alias MembersOnlyModel =
  -------------- Req'd arguments:
  { member : Maybe Member
  , nowBlock : Maybe (Maybe TimeBlock)
  , allTypes : Maybe (List TimeBlockType)
  -------------- Other state:
  , paymentInfoState : PaymentInfoState
  , badNews : List String
  }


init : Flags -> (MembersOnlyModel, Cmd Msg)
init flags =
  let sceneModel =
    { member = Nothing
    , nowBlock = Nothing
    , allTypes = Nothing
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

    MembersOnly ->
      if haveSomethingToSay kioskModel then
        -- We need to talk, so show this scene.
        (sceneModel, Cmd.none)
      else
        -- Nothing to say, so skip this scene.
        case sceneModel.member of
          Just m ->
            (sceneModel, send <| OldBusinessVector <| OB_SegueA (CheckInSession, m))
          Nothing ->
            (sceneModel, send <| ErrorVector <| ERR_Segue missingArguments)

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
    mship = sceneModel.member |> Maybe.andThen (.data >> .latestNonfutureMembership)
    membersOnlyStr = "Members Only"
    xis = kioskModel.xisSession
  in
    case (sceneModel.nowBlock, sceneModel.allTypes, mship) of

      -- Following is the case where somebody arrives during an explicit time block.
      (Just (Just nowBlock), Just allTypes, maybeMship) ->
        let
          isMembersOnly = xis.blockHasType membersOnlyStr allTypes nowBlock
        in
          case maybeMship of
            Just mship ->
              let current = xis.coverTime [mship] kioskModel.currTime
              in isMembersOnly && not current
            Nothing ->
              isMembersOnly

      -- Following is the case where we're not in any explicit time block.
      -- So use default time block type, if one has been specified.
      (Just Nothing, Just allTypes, maybeMship) ->
        let
          defaultBlockType = xis.defaultBlockType allTypes
          isMembersOnly =
            case defaultBlockType of
              Just bt -> bt.data.name == membersOnlyStr
              Nothing -> False
        in
          case maybeMship of
            Just mship ->
              let current = xis.coverTime [mship] kioskModel.currTime
              in isMembersOnly && not current
            Nothing ->
              isMembersOnly

      _ -> False


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : MembersOnlyMsg -> KioskModel a -> (MembersOnlyModel, Cmd Msg)
update msg kioskModel =

  let
    sceneModel = kioskModel.membersOnlyModel
    xis = kioskModel.xisSession

  in case msg of

    MO_Segue member nowBlock allTypes ->
      ( { sceneModel
        | member = Just member
        , nowBlock = Just nowBlock
        , allTypes = Just allTypes
        }
      , send <| WizardVector <| Push <| MembersOnly
      )

    SendPaymentInfo ->
      let
        newModel = {sceneModel | paymentInfoState = SendingPaymentInfo}
        cmd = case sceneModel.member of
          Just m -> xis.emailMembershipInfo m.id (MembersOnlyVector << ServerSentPaymentInfo)
          Nothing -> send <| ErrorVector <| ERR_Segue missingArguments
      in
        (newModel, cmd)

    ServerSentPaymentInfo (Ok msg) ->
      let
        newModel = {sceneModel | paymentInfoState = PaymentInfoSent}
      in
        (newModel, Cmd.none)

    PayNowAtFrontDesk ->
      ({sceneModel | paymentInfoState = ExplainingHowToPayNow}, Cmd.none)

    -- FAILURES --------------------

    ServerSentPaymentInfo (Err error) ->
      -- We will pretend it worked but will log the error.
      let
        msg = toString error |> Debug.log "Error trying to send payment info"
      in
        ( {sceneModel | paymentInfoState = PaymentInfoSent}
        , Cmd.none
        )


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.membersOnlyModel
    xis = kioskModel.xisSession
  in
    case sceneModel.member of

      Nothing ->
          errorView kioskModel missingArguments

      Just m ->

        genericScene kioskModel
          "Supporting Members Only"
          "Is your supporting membership up to date?"
          (
          case sceneModel.paymentInfoState of
            AskingIfMshipCurrent -> areYouCurrentContent kioskModel sceneModel xis m
            SendingPaymentInfo -> areYouCurrentContent kioskModel sceneModel xis m
            PaymentInfoSent -> paymentInfoSentContent kioskModel sceneModel xis m
            ExplainingHowToPayNow -> howToPayNowContent kioskModel sceneModel xis m
          )
          []  -- No buttons here. They will be woven into content.
          []  -- No bad news. Scene will fail silently, but should log somewhere.


areYouCurrentContent : KioskModel a -> MembersOnlyModel -> XisApi.Session Msg -> Member -> Html Msg
areYouCurrentContent kioskModel sceneModel xis member =
  let
    however = "However, you may have made a more recent payment that we haven't yet processed."
    paymentMsg = case member.data.latestNonfutureMembership of
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
        , sceneButton kioskModel (ButtonSpec "Send Me Payment Info" (MembersOnlyVector <| SendPaymentInfo) True)
        , vspace 20
        , sceneButton kioskModel (ButtonSpec "Pay Now at Front Desk" (MembersOnlyVector <| PayNowAtFrontDesk) True)
          -- TODO: If visitor is a keyholder, offer them 1day for $10
        , vspace 40
        , text "If your membership is current, thanks!"
        , vspace 0
        , text "Just click below."
        , vspace 20
        , sceneButton kioskModel
            <| ButtonSpec
               "I'm Current!"
               (OldBusinessVector <| OB_SegueA (CheckInSession, member))
               True
        ]


paymentInfoSentContent : KioskModel a -> MembersOnlyModel -> XisApi.Session Msg -> Member -> Html Msg
paymentInfoSentContent kioskModel sceneModel xis member =
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
      , sceneButton kioskModel
          <| ButtonSpec
              "OK"
              (OldBusinessVector <| OB_SegueA (CheckInSession, member))
              True
      ]

howToPayNowContent : KioskModel a -> MembersOnlyModel -> XisApi.Session Msg -> Member -> Html Msg
howToPayNowContent kioskModel sceneModel xis member =
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
    , sceneButton kioskModel
        <| ButtonSpec
             "OK"
             (OldBusinessVector <| OB_SegueA (CheckInSession, member))
             True
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
