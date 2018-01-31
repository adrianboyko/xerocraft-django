
module CheckOutScene exposing (init, view, sceneWillAppear, update, CheckOutModel)

-- Standard
import Html exposing (..)
import Http

-- Third Party
import Material
import Material.Chip as Chip
import Material.Options as Options exposing (css)
import List.Extra as ListX

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
  { checkedInAccts : List XisApi.Member
  , checkedOutMemberNum : Int  -- TODO: This should be Member not ID.
  , badNews : List String
  }

init : Flags -> (CheckOutModel, Cmd Msg)
init flags =
  let model =
    { checkedInAccts=[]
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
      tagger = (CheckOutVector << AccCheckedInAccts)
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

    AccCheckedInAccts (Ok {next, results}) ->
      -- TODO: This should add member to accumulator when evt type is ARRIVAL
      -- TODO: This should remove member from accumulator when evt type is DEPARTURE
      let
        currList = sceneModel.checkedInAccts
        moreForList = List.map (.data >> .who) results
        newList = (currList++moreForList)
          |> ListX.uniqueBy .id
          |> List.sortBy (.data >> .userName >> String.toLower)
        newModel = {sceneModel | checkedInAccts=newList }
        nextCmd = case next of
          Nothing -> Cmd.none
          Just url -> xis.moreVisitEvents url (CheckOutVector << AccCheckedInAccts)
      in (newModel, nextCmd)

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

    AccCheckedInAccts (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

    LogCheckOutResult (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)


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
              [ List.map memb2chip sceneModel.checkedInAccts
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
