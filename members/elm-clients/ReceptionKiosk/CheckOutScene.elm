
module ReceptionKiosk.CheckOutScene exposing (init, view, update)

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
import ReceptionKiosk.Backend as Backend exposing (getCheckedInAccts)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

init : Flags -> (CheckOutModel, Cmd Msg)
init flags =
  let model = { checkedInAccts=[], badNews=[], checkedInAcctsUrl=flags.checkedInAcctsUrl }
  in (model, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : CheckOutMsg -> Model -> (CheckOutModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.checkOutModel
  in case msg of

    CheckOutSceneWillAppear ->
      let
        url = sceneModel.checkedInAcctsUrl ++ "?format=json"  -- Easier than an "Accept" header.
        request = getCheckedInAccts url (CheckOutVector << UpdateCheckedInAccts)
      in
        (sceneModel, request)


    UpdateCheckedInAccts (Ok {target, matches}) ->
      let newModel = {sceneModel | checkedInAccts = matches}
      in (newModel, Cmd.none)

    UpdateCheckedInAccts (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

    LogCheckOut memberNum ->
      -- TODO: L. Might be last feature to be implemented to avoid collecting bogus visits during alpha testing.
      (sceneModel, send (Push CheckOutDone))

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : Model -> Html Msg
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
      (div [] (List.map acct2chip sceneModel.checkedInAccts))
      []  -- No buttons

-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

sceneChipCss =
  [ css "margin-left" "3px"
  , css "margin-right" "3px"
  ]
