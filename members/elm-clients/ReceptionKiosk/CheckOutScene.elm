
module ReceptionKiosk.CheckOutScene exposing (init, view, update, CheckOutModel)

-- Standard
import Html exposing (..)
import Http

-- Third Party
import Material
import Material.Chip as Chip
import Material.Options as Options exposing (css)

-- Local
import ReceptionKiosk.Types exposing (..)
import ReceptionKiosk.SceneUtils exposing (..)
import ReceptionKiosk.Backend as Backend

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias CheckOutModel =
  { checkedInAccts : List Backend.MatchingAcct
  , badNews : List String
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a = (SceneUtilModel {a | checkOutModel : CheckOutModel})

init : Flags -> (CheckOutModel, Cmd Msg)
init flags =
  let model = { checkedInAccts=[], badNews=[] }
  in (model, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : CheckOutMsg -> KioskModel a -> (CheckOutModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.checkOutModel
  in case msg of

    CheckOutSceneWillAppear ->
      let
        getCheckedInAccts = Backend.getCheckedInAccts kioskModel.flags
        request = getCheckedInAccts (CheckOutVector << UpdateCheckedInAccts)
      in
        (sceneModel, request)


    UpdateCheckedInAccts (Ok {target, matches}) ->
      let newModel = {sceneModel | checkedInAccts = matches}
      in (newModel, Cmd.none)

    UpdateCheckedInAccts (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

    LogCheckOut memberNum ->
      -- TODO: L. Might be last feature to be implemented to avoid collecting bogus visits during alpha testing.
      (sceneModel, send (WizardVector <| Push <| CheckOutDone))

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
              , [ formatBadNews sceneModel.badNews ]
              ]
          )
      )
      []  -- No buttons

-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

sceneChipCss =
  [ css "margin-left" "3px"
  , css "margin-right" "3px"
  ]
