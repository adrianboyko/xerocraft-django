
module ReasonForVisitScene exposing (init, update, view, ReasonForVisitModel)

-- Standard
import Html exposing (Html, text, div, span)
import Html.Attributes exposing (style)

-- Third Party
import Material
import Material.Toggles as Toggles
import Material.Options as Options exposing (css)
import Material.List as Lists
import List.Nonempty exposing (Nonempty)

-- Local
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import DjangoRestFramework exposing (PageOf)
import XisRestApi as XisApi exposing
  ( VisitEventReason(..)
  , VisitEventMethod(..)
  , VisitEventType(..)
  , Member
  )
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
  , reasonForVisitModel : ReasonForVisitModel
  , xisSession : XisApi.Session Msg
  , currTime : PointInTime
  }


type alias ReasonForVisitModel =
  { member : Maybe Member
  -- mode is always KioskCheckIn for this scene, so it doesn't require state.
  , reasonForVisit : Maybe VisitEventReason
  , badNews: List String
  }

init : Flags -> (ReasonForVisitModel, Cmd Msg)
init flags =
  ( { member = Nothing
    , reasonForVisit = Nothing
    , badNews = []
    }
  , Cmd.none
  )

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : ReasonForVisitMsg -> KioskModel a -> (ReasonForVisitModel, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.reasonForVisitModel
    xis = kioskModel.xisSession

  in case msg of

    R4V_Segue member ->
      ( {sceneModel | member = Just member}
      , send <| WizardVector <| Push <| ReasonForVisit
      )

    UpdateReasonForVisit reason ->
      ({sceneModel | reasonForVisit=Just reason, badNews=[]}, Cmd.none)

    ValidateReason ->

      case sceneModel.reasonForVisit of
        Nothing ->
          ({sceneModel | badNews = ["You must choose an activity type."]}, Cmd.none)
        Just reasonForVisit ->
          let
            cmd = case sceneModel.member of
              Just m ->
                xis.createVisitEvent
                  { who = xis.memberUrl m.id
                  , when = kioskModel.currTime
                  , eventType = VET_Arrival
                  , reason = Just reasonForVisit
                  , method = VEM_FrontDesk
                  }
                  (ReasonForVisitVector << LogCheckInResult)
              Nothing ->
                send <| ErrorVector <| ERR_Segue missingArguments
          in (sceneModel, cmd)

    LogCheckInResult (Ok _) ->
      case sceneModel.reasonForVisit of

        Just VER_Volunteer ->
          ( sceneModel
          , case sceneModel.member of
              Just m -> send <| TaskListVector <| TL_Segue m
              Nothing -> send <| ErrorVector <| ERR_Segue missingArguments
          )

        Just VER_Member ->
          ( sceneModel
          , case sceneModel.member of
              Just m -> send <| MembersOnlyVector <| MO_Segue m
              Nothing -> send <| ErrorVector <| ERR_Segue missingArguments
          )

        _ ->
          ( sceneModel
          , case sceneModel.member of
              Just m -> send <| OldBusinessVector <| OB_SegueA (CheckInSession, m)
              Nothing -> send <| ErrorVector <| ERR_Segue missingArguments
          )

    LogCheckInResult (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

reasonString : KioskModel a -> VisitEventReason -> String
reasonString kioskModel reason =
  case reason of
    VER_Curious -> "Checking out " ++ kioskModel.flags.orgName
    VER_Class -> "Attending a class or workshop"
    VER_Member -> "Personal project"
    VER_Club -> "Club activity (FRC, VEX, PEC)"
    VER_Guest -> "Guest of a paying member"
    VER_Volunteer -> "Volunteering or staffing"
    VER_Other -> "Other"

view : KioskModel a -> Html Msg
view kioskModel =
  let sceneModel = kioskModel.reasonForVisitModel
  in genericScene kioskModel
    "Today's Activity"
    "Let us know what you'll be doing today"
    ( div []
        [ makeActivityList kioskModel
           [ VER_Class
           , VER_Curious
           , VER_Member
           , VER_Club
           , VER_Volunteer
           , VER_Guest
           , VER_Other
           ]
        ]
    )
    [ButtonSpec "OK" (ReasonForVisitVector <| ValidateReason) True]
    sceneModel.badNews

makeActivityList : KioskModel a -> List VisitEventReason -> Html Msg
makeActivityList kioskModel reasons =
  let
    sceneModel = kioskModel.reasonForVisitModel
    reasonMsg reason = ReasonForVisitVector <| UpdateReasonForVisit <| reason
  in
    div [reasonListStyle]
      (
        [vspace 30]
        ++
        (List.indexedMap
          (\index reason ->
            div [reasonDivStyle]
              [ Toggles.radio MdlVector [mdlIdBase ReasonForVisit + index] kioskModel.mdl
                  [ Toggles.value
                      (case sceneModel.reasonForVisit of
                        Nothing -> False
                        Just r -> r == reason
                      )
                  , Options.onToggle (reasonMsg reason)
                  ]
                  [text (reasonString kioskModel reason)]
              ]
          )
          reasons
        )
      )


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

reasonListStyle = style
  [ "width" => "450px"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "text-align" => "left"
  ]

reasonDivStyle = style
  [ "background-color" => "#eeeeee"
  , "padding" => "10px"
  , "margin" => "15px"
  , "border-radius" => "20px"
  ]
