
module CheckOutDoneScene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , CheckOutDoneModel
  )

-- Standard
import Html exposing (Html, div, text)
import Time exposing (Time)

-- Third Party
import Material
import List.Nonempty exposing (Nonempty)

-- Local
import Types exposing (..)
import Wizard.SceneUtils exposing (..)
import XisRestApi as XisApi exposing (Member)
import PointInTime exposing (PointInTime)


-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------


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
  , checkOutDoneModel : CheckOutDoneModel
  , xisSession : XisApi.Session Msg
  , currTime : PointInTime
  }

type alias CheckOutDoneModel =
  { member : Maybe Member
  , logOpDone : Bool
  }

init : Flags -> (CheckOutDoneModel, Cmd Msg)
init flags =
  ( { member = Nothing
    , logOpDone = False
    }
  , Cmd.none
  )


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> Scene -> (CheckOutDoneModel, Cmd Msg)
sceneWillAppear kioskModel appearing vanishing =
  let
    sceneModel = kioskModel.checkOutDoneModel
  in
    if appearing == CheckOutDone then
      case sceneModel.member of
        Nothing ->
          (sceneModel, send <| ErrorVector <| ERR_Segue missingArguments)
        Just m ->
          let
            xis = kioskModel.xisSession
            newVisitEvent =
              { who = xis.memberUrl m.id
              , when = kioskModel.currTime
              , eventType = XisApi.VET_Departure
              , reason = Nothing
              , method = XisApi.VEM_FrontDesk
              }
            tagger = CheckOutDoneVector << COD_LogCheckOutResult
            recordVisitCmd = xis.createVisitEvent newVisitEvent tagger
          in
            ({sceneModel|logOpDone=False}, Cmd.batch [recordVisitCmd, rebase])
    else
      -- Ignore appearance of all other scenes.
      (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : CheckOutDoneMsg -> KioskModel a -> (CheckOutDoneModel, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.checkOutDoneModel
    xis = kioskModel.xisSession

  in case msg of

    COD_Segue member ->
      ( { sceneModel | member = Just member}
      , send <| WizardVector <| Push CheckOutDone
      )

    COD_LogCheckOutResult (Ok _) ->
      ({sceneModel | logOpDone=True}, Cmd.none)

    -- ERRORS -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

    COD_LogCheckOutResult (Err error) ->
      let
        _ = Debug.log "COD" (toString error)
      in
        ({sceneModel | logOpDone=True}, Cmd.none)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let sceneModel = kioskModel.checkOutDoneModel
  in genericScene kioskModel
    "You're Checked Out"
    "Have a Nice Day!"
    (vspace 40)
    ( if sceneModel.logOpDone then
        [ButtonSpec "Ok" msgForReset True]
      else
        []
    )
    [] -- Never any bad news for this scene


-----------------------------------------------------------------------------
-- TICK (called each second)
-----------------------------------------------------------------------------

