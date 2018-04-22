
module ReasonForVisitScene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , ReasonForVisitModel
  )

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
  ( TimeBlock
  , TimeBlockType
  , VisitEventReason(..)
  , VisitEventMethod(..)
  , VisitEventType(..)
  , Member
  )
import PointInTime exposing (PointInTime)
import Fetchable exposing (..)


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
  , nowBlock : Fetchable (Maybe TimeBlock)
  , allTypes : Fetchable (List TimeBlockType)
  , reasonForVisit : Maybe VisitEventReason
  , badNews: List String
  }

init : Flags -> (ReasonForVisitModel, Cmd Msg)
init flags =
  ( { member = Nothing
    , nowBlock = Pending
    , allTypes = Pending
    , reasonForVisit = Nothing
    , badNews = []
    }
  , Cmd.none
  )


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> Scene -> (ReasonForVisitModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene vanishingScene =
  let sceneModel = kioskModel.reasonForVisitModel
  in case appearingScene of

    -- We want to have the current time block on hand by the time ReasonForVisit
    -- appears, so start the fetch when welcome scenes appear.
    Welcome -> getTimeBlocks kioskModel
    WelcomeForRfid -> getTimeBlocks kioskModel

    _ ->
      (sceneModel, Cmd.none)  -- Ignore all other scene appearances.

getTimeBlocks kioskModel =
  let
    sceneModel = kioskModel.reasonForVisitModel
    xis = kioskModel.xisSession
    cmd1 = xis.listTimeBlocks (ReasonForVisitVector << UpdateTimeBlocks)
    cmd2 = xis.listTimeBlockTypes (ReasonForVisitVector << UpdateTimeBlockTypes)
  in
    (sceneModel, Cmd.batch [cmd1, cmd2])


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

    UpdateTimeBlocks (Ok {results}) ->
      let
        nowBlocks = List.filter (xis.pitInBlock kioskModel.currTime) results
        nowBlock = List.head nowBlocks
      in
        ({sceneModel | nowBlock = Received nowBlock }, Cmd.none)

    UpdateTimeBlockTypes (Ok {results}) ->
      ({sceneModel | allTypes = Received results}, Cmd.none)

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
          , case (sceneModel.member, sceneModel.nowBlock, sceneModel.allTypes) of
              (Just m, Received nb, Received at) -> send <| MembersOnlyVector <| MO_Segue m nb at
              _ -> send <| ErrorVector <| ERR_Segue missingArguments
          )

        _ ->
          ( sceneModel
          , case sceneModel.member of
              Just m -> send <| OldBusinessVector <| OB_SegueA (CheckInSession, m)
              Nothing -> send <| ErrorVector <| ERR_Segue missingArguments
          )

    -- FAILURES --------------------

    LogCheckInResult (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

    UpdateTimeBlocks (Err error) ->
      let msg = toString error |> Debug.log "Error getting time blocks"
      in ({sceneModel | nowBlock = Failed msg}, Cmd.none)

    UpdateTimeBlockTypes (Err error) ->
      let msg = toString error |> Debug.log "Error getting time block types"
      in ({sceneModel | allTypes = Failed msg}, Cmd.none)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

reasonString : KioskModel a -> VisitEventReason -> String
reasonString kioskModel reason =
  case reason of
    VER_Class -> "Attending a class or workshop"
    VER_Club -> "Club activity (FRC, VEX, PEC)"
    VER_Curious -> "Checking out " ++ kioskModel.flags.orgName
    VER_Guest -> "Guest of a paying member"
    VER_Member -> "Membership privileges"
    VER_Other -> "Other"
    VER_PublicAccess -> "Free public access (Open Hack)"
    VER_Volunteer -> "Volunteering or staffing"

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.reasonForVisitModel
    xis = kioskModel.xisSession
    allBlockTypes = case sceneModel.allTypes of
      Received bts -> bts
      _ -> []  -- If this happens, it's because of unusually slow network
    isPublicAccessTime = case sceneModel.nowBlock of
      Received (Just nb) ->
        let
          openshop = xis.blockHasType "Open Shop" allBlockTypes nb
          wtf = xis.blockHasType "Women, Trans, Femme" allBlockTypes nb
        in
          openshop || wtf
      _ -> False  -- If this happens, it's because of unusually slow network
  in
    genericScene kioskModel
      "Today's Activity"
      "Let us know what you'll be doing today"
      ( div []
          [ makeActivityList kioskModel
             [ VER_Class
             , VER_Curious
             , if isPublicAccessTime then VER_PublicAccess else VER_Member
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
