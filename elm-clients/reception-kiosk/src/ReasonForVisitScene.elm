
module ReasonForVisitScene exposing (init, update, view, ReasonForVisitModel)

-- Standard
import Html exposing (Html, text, div, span)
import Html.Attributes exposing (style)

-- Third Party
import Material.Toggles as Toggles
import Material.Options as Options exposing (css)
import Material.List as Lists

-- Local
import MembersApi as MembersApi exposing (ReasonForVisit(..))
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import CheckInScene exposing (CheckInModel)

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

    UpdateReasonForVisit reason ->
      ({sceneModel | reasonForVisit = Just reason}, Cmd.none)

    ValidateReason ->

      case sceneModel.reasonForVisit of
        Nothing ->
          ({sceneModel | badNews = ["You must choose an activity type."]}, Cmd.none)
        Just reasonForVisit ->
          let
            logArrivalEventFn = MembersApi.logArrivalEvent kioskModel.flags
            msg = ReasonForVisitVector << LogCheckInResult
            visitingMemberPk = checkInModel.memberNum
            cmd = logArrivalEventFn visitingMemberPk reasonForVisit msg
          in (sceneModel, cmd)

    LogCheckInResult (Ok {result}) ->
      case sceneModel.reasonForVisit of
        Just Volunteer ->
          (sceneModel, segueTo TaskList)
        Just MemberPrivileges ->
          (sceneModel, segueTo CheckIn)
        _ ->
          (sceneModel, segueTo CheckInDone)

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
    MemberPrivileges -> "Personal project"
    GuestOfMember -> "Guest of a paying member"
    Volunteer -> "Volunteering or staffing"
    Other -> "Other"

view : KioskModel a -> Html Msg
view kioskModel =
  let sceneModel = kioskModel.reasonForVisitModel
  in genericScene kioskModel
    "Today's Activity"
    "Let us know what you'll be doing today"
    ( div []
        [ makeActivityList kioskModel
           [ ClassParticipant
           , Curiousity
           , MemberPrivileges
           , Volunteer
           , GuestOfMember
           , Other
           ]
        ]
    )
    [ButtonSpec "OK" (ReasonForVisitVector <| ValidateReason)]
    sceneModel.badNews

makeActivityList : KioskModel a -> List ReasonForVisit -> Html Msg
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
