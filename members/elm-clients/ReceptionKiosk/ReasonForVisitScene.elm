
module ReceptionKiosk.ReasonForVisitScene exposing (init, update, view)

-- Standard
import Html exposing (Html, text)

-- Third Party
import Material.Toggles as Toggles
import Material.Options as Options exposing (css)
import Material.List as Lists

-- Local
import ReceptionKiosk.Types exposing (..)
import ReceptionKiosk.SceneUtils exposing (..)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

init : Flags -> (ReasonForVisitModel, Cmd Msg)
init flags =
  let sceneModel = {reasonForVisit = Nothing}
  in (sceneModel, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : ReasonForVisitMsg -> Model -> (ReasonForVisitModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.reasonForVisitModel
  in case msg of

    UpdateReasonForVisit reason ->
      ({sceneModel | reasonForVisit = Just reason}, Cmd.none)

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

reasonString : Model -> ReasonForVisit -> String
reasonString kioskModel reason =
  case reason of
    Curiousity -> "Checking out " ++ kioskModel.flags.orgName
    ClassParticipant -> "Attending a class or workshop"
    MemberPrivileges -> "Working on a personal project"
    GuestOfMember -> "Guest of a paying member"
    Volunteer -> "Volunteering or staffing"
    Other -> "Other"

view : Model -> Html Msg
view kioskModel =
  genericScene kioskModel
    "Today's Activity"
    "Let us know what you'll be doing today"
    (makeActivityList kioskModel
      [ Curiousity
      , ClassParticipant
      , MemberPrivileges
      , GuestOfMember
      , Volunteer
      , Other
      ]
    )
    [ButtonSpec "OK" (Push CheckInDone)]

makeActivityList : Model -> List ReasonForVisit -> Html Msg
makeActivityList kioskModel reasons =
  let sceneModel = kioskModel.reasonForVisitModel
  in Lists.ul activityListCss
    (List.indexedMap
      ( \index reason ->
          Lists.li [css "font-size" "18pt"]
            [ Lists.content [] [text (reasonString kioskModel reason)]
            , Lists.content2 []
              [ Toggles.radio MdlVector [2000+index] kioskModel.mdl  -- 2000 establishes an id range for these.
                  [ Toggles.value
                      ( case sceneModel.reasonForVisit of
                          Nothing -> False
                          Just r -> r == reason
                      )
                  , Options.onToggle (ReasonForVisitVector (UpdateReasonForVisit reason))
                  ]
                  []
              ]
            ]
      )
      reasons
    )

-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

activityListCss =
  [ css "width" "450px"
  , css "margin-left" "auto"
  , css "margin-right" "auto"
  , css "margin-top" "80px"
  ]