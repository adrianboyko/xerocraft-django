
module ReceptionKiosk.CheckOutScene exposing (init, view, sceneWillAppear, update, CheckOutModel)

-- Standard
import Html exposing (..)
import Http

-- Third Party
import Material
import Material.Chip as Chip
import Material.Options as Options exposing (css)

-- Local
import ReceptionKiosk.Types exposing (..)
import Wizard.SceneUtils exposing (..)
import MembersApi as MembersApi

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias CheckOutModel =
  { checkedInAccts : List MembersApi.MatchingAcct
  , badNews : List String
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a = (SceneUtilModel {a | checkOutModel : CheckOutModel})

init : Flags -> (CheckOutModel, Cmd Msg)
init flags =
  let model = { checkedInAccts=[], badNews=[] }
  in (model, Cmd.none)

-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (CheckOutModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  if appearingScene == CheckOut
    then
      let
        getCheckedInAccts = MembersApi.getCheckedInAccts kioskModel.flags
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
      -- TODO: L. Might be last feature to be implemented to avoid collecting bogus visits during alpha testing.
      (sceneModel, segueTo CheckOutDone)

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
