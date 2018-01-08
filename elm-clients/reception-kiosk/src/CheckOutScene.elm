
module CheckOutScene exposing (init, view, sceneWillAppear, update, CheckOutModel)

-- Standard
import Html exposing (..)
import Http

-- Third Party
import Material
import Material.Chip as Chip
import Material.Options as Options exposing (css)

-- Local
import Types exposing (..)
import Wizard.SceneUtils exposing (..)
import MembersApi as MembersApi

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias CheckOutModel =
  { checkedInAccts : List MembersApi.MatchingAcct
  , checkedOutMemberNum : Int
  , badNews : List String
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  ( SceneUtilModel
    { a
    | checkOutModel : CheckOutModel
    , membersApi : MembersApi.Session Msg
    }
  )

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
  if appearingScene == CheckOut
    then
      let
        getCheckedInAccts = kioskModel.membersApi.getCheckedInAccts
        request = getCheckedInAccts (CheckOutVector << UpdateCheckedInAccts)
      in (kioskModel.checkOutModel, request)
    else
      (kioskModel.checkOutModel, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : CheckOutMsg -> KioskModel a -> (CheckOutModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.checkOutModel
  in case msg of

    UpdateCheckedInAccts (Ok {target, matches}) ->
      let newModel = {sceneModel | checkedInAccts = matches}
      in (newModel, Cmd.none)

    UpdateCheckedInAccts (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

    LogCheckOut memberNum ->
      let
        logDepartureEventFn = kioskModel.membersApi.logDepartureEvent
        msg = CheckOutVector << LogCheckOutResult
        visitingMemberPk = memberNum
        cmd = logDepartureEventFn visitingMemberPk msg
      in
        ({sceneModel | checkedOutMemberNum = memberNum}, cmd)

    LogCheckOutResult (Ok {result}) ->
      (sceneModel, segueTo TimeSheetPt1)

    LogCheckOutResult (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.checkOutModel
    acct2chip = \acct ->
      Chip.button
        [Options.onClick (CheckOutVector (LogCheckOut acct.memberNum))]
        [Chip.content [] [text acct.userName]]

  in
    genericScene kioskModel
      "Hope You Had Fun!"
      "Tap your userid, below:"
      ( div []
          ( List.concat
              [ List.map acct2chip sceneModel.checkedInAccts
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
