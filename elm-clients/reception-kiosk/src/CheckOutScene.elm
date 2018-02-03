
module CheckOutScene exposing (init, view, sceneWillAppear, update, CheckOutModel)

-- Standard
import Html exposing (..)
import Http

-- Third Party
import Material
import Material.Chip as Chip
import Material.Options as Options exposing (css)
import List.Extra as ListX
import Maybe.Extra as MaybeX

-- Local
import Types exposing (..)
import Wizard.SceneUtils exposing (..)
import XisRestApi as XisApi
import Duration exposing (ticksPerHour)
import PointInTime exposing (PointInTime)


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  ( SceneUtilModel
    { a
    | checkOutModel : CheckOutModel
    , currTime : PointInTime
    , xisSession : XisApi.Session Msg
    }
  )

type alias CheckOutModel =
  { visitEvents : List XisApi.VisitEvent
  , checkedIn : List XisApi.Member
  , checkedOutMemberNum : Int  -- TODO: This should be Member not ID.
  , badNews : List String
  }

init : Flags -> (CheckOutModel, Cmd Msg)
init flags =
  let model =
    { visitEvents=[]
    , checkedIn=[]
    , checkedOutMemberNum = -99  -- A harmless initial value.
    , badNews=[]
    }
  in (model, Cmd.none)

-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (CheckOutModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  if appearingScene == CheckOut then
    let
      lowerBound = kioskModel.currTime - (24 * ticksPerHour)
      filters = [ XisApi.VEF_WhenGreaterOrEquals lowerBound ]
      tagger = (CheckOutVector << AccVisitEvents)
      cmd = kioskModel.xisSession.listVisitEvents filters tagger
    in
      (kioskModel.checkOutModel, cmd)
  else
    (kioskModel.checkOutModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : CheckOutMsg -> KioskModel a -> (CheckOutModel, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.checkOutModel
    xis = kioskModel.xisSession
  in case msg of

    AccVisitEvents (Ok {next, results}) ->
      let
        ves = sceneModel.visitEvents ++ results
        newModel = {sceneModel | visitEvents=ves }
      in
        case next of

          Just url ->
            (newModel, xis.moreVisitEvents url (CheckOutVector << AccVisitEvents))

          Nothing ->
            let
              checkedIn = checkedInMembers newModel.visitEvents
              newModel2 = {sceneModel | checkedIn=checkedIn, visitEvents=[] }
            in
              (newModel2, Cmd.none)

    LogCheckOut memberNum ->
      let
        newVisitEvent =
          { who = xis.memberUrl memberNum
          , when = kioskModel.currTime
          , eventType = XisApi.VET_Departure
          , reason = Nothing
          , method = XisApi.VEM_FrontDesk
          }
        tagger = CheckOutVector << LogCheckOutResult
        cmd = xis.createVisitEvent newVisitEvent tagger
      in
        ({sceneModel | checkedOutMemberNum = memberNum}, cmd)

    LogCheckOutResult (Ok _) ->
      (sceneModel, segueTo OldBusiness)

    -- ERRORS -------------------------

    AccVisitEvents (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

    LogCheckOutResult (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)


checkedInMembers : List XisApi.VisitEvent -> List XisApi.Member
checkedInMembers events =
  let
    whoId = .data >> .who >> .id
    visitGrouper x y = whoId x == whoId y
    arrivalFilter x = x.data.eventType == XisApi.VET_Arrival
  in
    events                                          -- List VisitEvent
    |> List.sortBy whoId                            -- List VisitEvent
    |> ListX.groupWhile visitGrouper                -- List (List VisitEvent)
    |> List.map (ListX.maximumBy (.data >> .when))  -- List (Maybe VisitEvent)
    |> MaybeX.combine                               -- Maybe (List VisitEvent)
    |> Maybe.withDefault []                         -- List VisitEvent
    |> List.filter arrivalFilter
    |> List.map (.data >> .who)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.checkOutModel
    memb2chip = \memb ->
      Chip.button
        [Options.onClick (CheckOutVector (LogCheckOut memb.id))]
        [Chip.content [] [text memb.data.userName]]

  in
    genericScene kioskModel
      "Checking Out"
      "Tap Your Userid, Below"
      ( div []
          ( List.concat
              [ List.map memb2chip sceneModel.checkedIn
              , [ vspace (if List.length sceneModel.badNews > 0 then 40 else 0) ]
              ]
          )
      )
      []  -- No buttons
      sceneModel.badNews

-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

sceneChipCss =
  [ css "margin-left" "3px"
  , css "margin-right" "3px"
  ]
