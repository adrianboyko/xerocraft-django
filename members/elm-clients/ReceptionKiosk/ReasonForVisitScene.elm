
module ReceptionKiosk.ReasonForVisitScene exposing (init, update, view, ReasonForVisitModel)

-- Standard
import Html exposing (Html, text, div, span)
import Html.Attributes exposing (style)

-- Third Party
import Material.Toggles as Toggles
import Material.Options as Options exposing (css)
import Material.List as Lists

-- Local
import MembersApi as MembersApi exposing (ReasonForVisit(..))
import TaskApi exposing (..)
import Wizard.SceneUtils exposing (..)
import ReceptionKiosk.Types exposing (..)
import ReceptionKiosk.CheckInScene exposing (CheckInModel)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  (SceneUtilModel
    { a
    | reasonForVisitModel : ReasonForVisitModel
    , checkInModel : CheckInModel
    , flags : Flags
    }
  )

type alias ReasonForVisitModel =
  { reasonForVisit: Maybe ReasonForVisit
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

  in case msg of

    ReasonForVisitSceneWillAppear ->
      -- Start fetching workable tasks NOW in case they choose the "volunteering" reason.
      let
        request = getCurrCalendarPageForMember
          kioskModel.flags.csrfToken
          checkInModel.memberNum
          (TaskListVector << CalendarPageResult)

      in (sceneModel, request)

    UpdateReasonForVisit reason ->
      ({sceneModel | reasonForVisit = Just reason}, Cmd.none)

    ValidateReason ->

      case sceneModel.reasonForVisit of
        Nothing ->
          ({sceneModel | badNews = ["You must choose an activity type."]}, Cmd.none)
        Just reasonForVisit ->
          let
            logVisitEvent = MembersApi.logVisitEvent  kioskModel.flags
            msg = ReasonForVisitVector << LogCheckInResult
            visitingMemberPk = checkInModel.memberNum
            cmd = logVisitEvent visitingMemberPk MembersApi.Arrival reasonForVisit msg
          in (sceneModel, cmd)

    LogCheckInResult (Ok {result}) ->
      case sceneModel.reasonForVisit of
        Just Volunteer ->
          (sceneModel, send (WizardVector <| Push <| TaskList))
        _ ->
          (sceneModel, send (WizardVector <| Push <| CheckInDone))

    LogCheckInResult (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

reasonString : KioskModel a -> ReasonForVisit -> String
reasonString kioskModel reason =
  case reason of
    Curiousity -> "Checking out " ++ kioskModel.flags.orgName
    ClassParticipant -> "Attending a class or workshop"
    MemberPrivileges -> "Membership privileges"
    GuestOfMember -> "Guest of a paying member"
    Volunteer -> "Volunteering or staffing"
    Other -> "Other"

view : KioskModel a -> Html Msg
view kioskModel =
  genericScene kioskModel
    "Today's Activity"
    "Let us know what you'll be doing today"
    ( div []
        [ makeActivityList kioskModel
           [ MemberPrivileges
           , Volunteer
           , Curiousity
           , ClassParticipant
           , GuestOfMember
           , Other
           ]
        , formatBadNews kioskModel.reasonForVisitModel.badNews
        ]
    )
    [ButtonSpec "OK" (ReasonForVisitVector <| ValidateReason)]

makeActivityList : KioskModel a -> List ReasonForVisit -> Html Msg
makeActivityList kioskModel reasons =
  let
    sceneModel = kioskModel.reasonForVisitModel
    reasonMsg reason = ReasonForVisitVector <| UpdateReasonForVisit <| reason
  in
    div [reasonListStyle]
      (
        [vspace 50]
        ++
        (List.indexedMap
          (\index reason ->
            span []
              [ Toggles.radio MdlVector [mdlIdBase ReasonForVisit + index] kioskModel.mdl
                  [ Toggles.value
                      (case sceneModel.reasonForVisit of
                        Nothing -> False
                        Just r -> r == reason
                      )
                  , Options.onToggle (reasonMsg reason)
                  ]
                  [text (reasonString kioskModel reason)]
              , vspace 30
              ]
          )
          reasons
        )
      )


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

reasonListStyle = style
  [ "width" => "350px"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "padding-left" => "45px"
  , "text-align" => "left"
  ]

