
module ReceptionKiosk.WelcomeScene exposing (init, update, view, WelcomeModel)

-- Standard
import Html exposing (..)

-- Third Party

-- Local
import ReceptionKiosk.Types exposing (..)
import ReceptionKiosk.SceneUtils exposing (..)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias WelcomeModel =
  {
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a = (SceneUtilModel {a | welcomeModel : WelcomeModel})

init : Flags -> (WelcomeModel, Cmd Msg)
init flags = ({}, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : WelcomeMsg -> KioskModel a -> (WelcomeModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.welcomeModel
  in case msg of

    WelcomeSceneWillAppear ->
      let sceneModel = kioskModel.welcomeModel
      in (sceneModel, send Reset)

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  genericScene kioskModel
    "Welcome!"
    "Choose one of the following:"
    (text "")
    [ ButtonSpec "I'm new!" (Push DoYouHaveAcct)
    , ButtonSpec "Check In" (Push CheckIn)
    , ButtonSpec "Check Out" (Push CheckOut)
    ]

