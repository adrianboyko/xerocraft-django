
module ReasonForVisitScene exposing (init, update, view, ReasonForVisitModel)

-- Standard
import Html exposing (Html, text, div, span)
import Html.Attributes exposing (style)

-- Third Party
import Material.Toggles as Toggles
import Material.Options as Options exposing (css)
import Material.List as Lists

-- Local
import MembersApi as MembersApi exposing (ReasonForVisit(..), GenericResult)
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import CheckInScene exposing (CheckInModel)
import DjangoRestFramework exposing (PageOf)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  (SceneUtilModel
    { a
    | reasonForVisitModel : ReasonForVisitModel
    , checkInModel : CheckInModel
    , membersApi : MembersApi.Session Msg
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
      ({sceneModel | reasonForVisit=Just reason, badNews=[]}, Cmd.none)

    ValidateReason ->

      case sceneModel.reasonForVisit of
        Nothing ->
          ({sceneModel | badNews = ["You must choose an activity type."]}, Cmd.none)
        Just reasonForVisit ->
          let
            logArrivalEventFn = kioskModel.membersApi.logArrivalEvent
            tagger = ReasonForVisitVector << LogCheckInResult
            cmd = case checkInModel.checkedInMember of
              Just m -> logArrivalEventFn m.id reasonForVisit tagger
              Nothing ->
                -- We shouldn't get to this scene without there being a checkedInMember.
                -- If it actually happens, log a message and fake success to get us to next scene.
                let _ = Debug.log "checkedInMember" Nothing
                in GenericResult "ARBITRARY" |> Ok |> tagger |> send
          in (sceneModel, cmd)

    LogCheckInResult (Ok _) ->
      case sceneModel.reasonForVisit of
        Just Volunteer ->
          (sceneModel, segueTo TaskList)
        Just MemberPrivileges ->
          (sceneModel, segueTo MembersOnly)
        _ ->
          (sceneModel, segueTo OldBusiness)

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
    ClubPrivileges -> "Club activity (FRC, VEX, PEC)"
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
           , ClubPrivileges
           , Volunteer
           , GuestOfMember
           , Other
           ]
        ]
    )
    [ButtonSpec "OK" (ReasonForVisitVector <| ValidateReason) True]
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
