
module CheckOutScene exposing
  ( init
  , rfidWasSwiped
  , sceneWillAppear
  , update
  , view
  --------------
  , CheckOutModel
  )

-- Standard
import Html exposing (..)
import Http

-- Third Party
import Material
import Material.Chip as Chip
import Material.Options as Options exposing (css)
import List.Extra as ListX
import Maybe.Extra as MaybeX
import List.Nonempty exposing (Nonempty)

-- Local
import Types exposing (..)
import Wizard.SceneUtils exposing (..)
import XisRestApi as XisApi exposing (Member)
import Duration exposing (ticksPerHour)
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
  , checkOutModel : CheckOutModel
  , currTime : PointInTime
  , xisSession : XisApi.Session Msg
  }

type alias CheckOutModel =
  { visitEvents : List XisApi.VisitEvent
  , checkedIn : List Member
  , badNews : List String
  }

init : Flags -> (CheckOutModel, Cmd Msg)
init flags =
  let model =
    { visitEvents = []
    , checkedIn = []
    , badNews = []
    }
  in (model, Cmd.none)

-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (CheckOutModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  if appearingScene == CheckOut then
    let
      lowerBound = kioskModel.currTime - (12 * ticksPerHour)
      filters = [ XisApi.VEF_WhenGreaterOrEquals lowerBound ]
      tagger = (CheckOutVector << CO_AccVisitEvents)
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

    CO_AccVisitEvents (Ok {next, results}) ->
      let
        ves = sceneModel.visitEvents ++ results
        newModel = {sceneModel | visitEvents=ves }
      in
        case next of

          Just url ->
            (newModel, xis.moreVisitEvents url (CheckOutVector << CO_AccVisitEvents))

          Nothing ->
            let
              sorter = List.sortBy (.data >> .userName >> String.toLower)
              checkedIn = newModel.visitEvents |> checkedInMembers |> sorter
              newModel2 = {sceneModel | checkedIn=checkedIn, visitEvents=[] }
            in
              (newModel2, Cmd.none)

    CO_MemberChosen m ->
      (sceneModel, send <| OldBusinessVector <| OB_SegueA (CheckOutSession, m))

    -- ERRORS -------------------------

    CO_AccVisitEvents (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)


checkedInMembers : List XisApi.VisitEvent -> List Member
checkedInMembers events =
  let
    whoId = .data >> .who >> .id
    visitGrouper x y = whoId x == whoId y
    stillHereFilter x = List.member x.data.eventType [XisApi.VET_Arrival, XisApi.VET_Present]
  in
    events                                          -- List VisitEvent
    |> List.sortBy whoId                            -- List VisitEvent
    |> ListX.groupWhile visitGrouper                -- List (List VisitEvent)
    |> List.map (ListX.maximumBy (.data >> .when))  -- List (Maybe VisitEvent)
    |> MaybeX.combine                               -- Maybe (List VisitEvent)
    |> Maybe.withDefault []                         -- List VisitEvent
    |> List.filter stillHereFilter
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
        [Options.onClick (CheckOutVector (CO_MemberChosen memb))]
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
-- RFID WAS SWIPED
-----------------------------------------------------------------------------

rfidWasSwiped : KioskModel a -> Result String Member -> (CheckOutModel, Cmd Msg)
rfidWasSwiped kioskModel result =
  case result of
    Ok m ->
      update (CO_MemberChosen m) kioskModel
    Err e ->
      let sceneModel = kioskModel.checkOutModel
      in ({sceneModel | badNews = [toString e]}, Cmd.none)


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

sceneChipCss =
  [ css "margin-left" "3px"
  , css "margin-right" "3px"
  ]
