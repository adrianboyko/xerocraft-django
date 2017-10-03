
module CheckOutDoneScene exposing (init, view, tick, CheckOutDoneModel)

-- Standard
import Html exposing (Html, div, text)
import Time exposing (Time)

-- Third Party

-- Local
import Types exposing (..)
import Wizard.SceneUtils exposing (..)


-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------

displayTimeout = 5


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias CheckOutDoneModel =
  { displayTimeRemaining : Int
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a = (SceneUtilModel {a | checkOutDoneModel : CheckOutDoneModel})

-- TODO: There should be a time out back to Welcome
init : Flags -> (CheckOutDoneModel, Cmd Msg)
init flags = ({displayTimeRemaining=displayTimeout}, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let sceneModel = kioskModel.checkOutDoneModel
  in genericScene kioskModel
    "You're Checked Out"
    "Have a Nice Day!"
    ( div []
      [ vspace 40
      , sceneButton kioskModel <| ButtonSpec "Ok" (WizardVector <| Push <| Welcome)
      , vspace 70
      , (text (String.repeat sceneModel.displayTimeRemaining "●"))
      ]
    )
    []
    [] -- Never any bad news for this scene


-----------------------------------------------------------------------------
-- TICK (called each second)
-----------------------------------------------------------------------------

tick : Time -> KioskModel a -> (CheckOutDoneModel, Cmd Msg)
tick time kioskModel =
  let
    sceneModel = kioskModel.checkOutDoneModel
    visible = sceneIsVisible kioskModel CheckOutDone
    dec = if visible then 1 else 0
    newTimeRemaining = sceneModel.displayTimeRemaining - dec
    cmd = if newTimeRemaining <= 0 then segueTo Welcome else Cmd.none
  in
    ({sceneModel | displayTimeRemaining=newTimeRemaining}, cmd)
