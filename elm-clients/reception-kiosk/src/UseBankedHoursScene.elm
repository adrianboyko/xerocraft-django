
module UseBankedHoursScene exposing
  ( init
  , update
  , view
  , UseBankedHoursModel
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
import PointInTime exposing (PointInTime)


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
  , useBankedHoursModel : UseBankedHoursModel
  , currTime : Time
  , xisSession : XisApi.Session Msg
  }


type alias UseBankedHoursModel =
  -------------- Req'd arguments:
  { member : Maybe Member
  -------------- Other state:
  , badNews : List String
  }


init : Flags -> (UseBankedHoursModel, Cmd Msg)
init flags =
  let sceneModel =
    { member = Nothing
    , badNews = []
    }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : UseBankedHoursMsg -> KioskModel a -> (UseBankedHoursModel, Cmd Msg)
update msg kioskModel =

  let
    sceneModel = kioskModel.useBankedHoursModel
    xis = kioskModel.xisSession

  in case msg of

    UBH_Segue member ->

      let
        newSceneModel = { sceneModel | member = Just member }
      in
        (newSceneModel, send <| WizardVector <| Push UseBankedHours)

    UseSomeHours_Clicked member ->
      let
        searchPlay = xis.listPlays
          [ PlayingMemberEquals member.id
          , PlayDateEquals (PointInTime.toCalendarDate kioskModel.currTime)
          , PlayDurationIsNull True
          ]
          (UseBankedHoursVector << (PlayList_Result member))
      in
        (sceneModel, searchPlay)

    PlayList_Result member (Ok {count}) ->
      let
        cmd = if count == 0 -- There is not yet a play record.
          then xis.createPlay
            { playDuration = Nothing
            , playDate = PointInTime.toCalendarDate kioskModel.currTime
            , playStartTime = Just <| PointInTime.toClockTime kioskModel.currTime
            , playingMember = xis.memberUrl member.id
            }
            (UseBankedHoursVector << (PlayCreation_Result member))
          else send <| OldBusinessVector <| OB_SegueA CheckInSession member
      in
        (sceneModel, cmd)

    PlayCreation_Result member (Ok _) ->
      (sceneModel, send <| OldBusinessVector <| OB_SegueA CheckInSession member)

    WillVolunteer_Clicked member ->
      -- TODO: What do we want to do here to track or encourage this pledge?
      (sceneModel, send <| UseBankedHoursVector <| UseSomeHours_Clicked member)


    -- FAILURES --------------------

    PlayCreation_Result member (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

    PlayList_Result member (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.useBankedHoursModel
    xis = kioskModel.xisSession
  in
    case sceneModel.member of

      Nothing ->
        errorView kioskModel missingArguments

      Just member ->
        let
          balance = Maybe.withDefault 0.0 member.data.worker.data.timeAcctBalance
        in
          if balance <= 0.0 then
            view_BadBalance kioskModel member balance
          else
            view_GoodBalance kioskModel member balance


view_GoodBalance kioskModel member balance =
  genericScene kioskModel
    "Your Banked Hours Balance"
    ""
    (div [sceneTextBlockStyle, sceneTextStyle]
      [ vspace 60
      , text <| "You have " ++ (toString balance) ++ " hour(s) banked! "
      , text <| "Because we offer a 2-for-1 deal, that's good for " ++ (toString <| 2.0*balance) ++ " hour(s) of membership privileges."
      , vspace 40
      , text <| "If you want to use some of this credit, you'll need to CHECK OUT when you're done so we know how much time to deduct."
      ]
    )
    [ButtonSpec "Got It!" (UseBankedHoursVector <| UseSomeHours_Clicked member) True]
    kioskModel.useBankedHoursModel.badNews


view_BadBalance kioskModel member balance =
  genericScene kioskModel
    "Your Banked Hours Balance"
    ""
    (div [sceneTextBlockStyle, sceneTextStyle]
      [ vspace 60
      , text <| "You have " ++ (toString balance) ++ " hour(s) banked. "
      , text <| "You're going to need to do some volunteer work to build up your balance."
      ]
    )
    [ ButtonSpec "I'll Volunteer" (UseBankedHoursVector <| WillVolunteer_Clicked member) True
    ]
    kioskModel.useBankedHoursModel.badNews


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

