
module ReasonForVisitScene exposing (init, update, view, ReasonForVisitModel)

-- Standard
import Html exposing (Html, text, div, span)
import Html.Attributes exposing (style)

-- Third Party
import Material.Toggles as Toggles
import Material.Options as Options exposing (css)
import Material.List as Lists

-- Local
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import CheckInScene exposing (CheckInModel)
import DjangoRestFramework exposing (PageOf)
import XisRestApi as XisApi exposing
  ( VisitEventReason(..)
  , VisitEventMethod(..)
  , VisitEventType(..)
  )
import PointInTime exposing (PointInTime)


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  (SceneUtilModel
    { a
    | reasonForVisitModel : ReasonForVisitModel
    , checkInModel : CheckInModel
    , xisSession : XisApi.Session Msg
    , currTime : PointInTime
    , flags : Flags
    }
  )

type alias ReasonForVisitModel =
  { reasonForVisit: Maybe VisitEventReason
  , badNews: List String
  }

init : Flags -> (ReasonForVisitModel, Cmd Msg)
init flags =
  let sceneModel = {reasonForVisit = Nothing, badNews = []}
  in (sceneModel, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : ReasonForVisitMsg -> KioskModel a -> (ReasonForVisitModel, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.reasonForVisitModel
    checkInModel = kioskModel.checkInModel
    xis = kioskModel.xisSession

  in case msg of

    UpdateReasonForVisit reason ->
      ({sceneModel | reasonForVisit=Just reason, badNews=[]}, Cmd.none)

    ValidateReason ->

      case sceneModel.reasonForVisit of
        Nothing ->
          ({sceneModel | badNews = ["You must choose an activity type."]}, Cmd.none)
        Just reasonForVisit ->
          let
            cmd = case checkInModel.checkedInMember of
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
                -- We shouldn't get to this scene without there being a checkedInMember.
                -- If it actually happens, log a message and fake success to get us to next scene.
                let _ = Debug.log "RFV ERROR" "No checked in member"
                in segueTo CheckInDone  -- REVIEW: Is this the best choice?
          in (sceneModel, cmd)

    LogCheckInResult (Ok _) ->
      case sceneModel.reasonForVisit of
        Just VER_Volunteer ->
          (sceneModel, segueTo TaskList)
        Just VER_Member ->
          (sceneModel, segueTo MembersOnly)
        _ ->
          (sceneModel, segueTo OldBusiness)

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
