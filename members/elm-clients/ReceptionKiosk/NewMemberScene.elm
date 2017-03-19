
module ReceptionKiosk.NewMemberScene exposing (init, update, view)

-- Standard
import Html exposing (Html, div)
import Http

-- Third Party

-- Local
import ReceptionKiosk.Backend as Backend
import ReceptionKiosk.Types exposing (..)
import ReceptionKiosk.SceneUtils exposing (..)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

init : Flags -> (NewMemberModel, Cmd Msg)
init flags =
  let model =
   { firstName = ""
   , lastName = ""
   , email = ""
   , isAdult = False
   }
  in (model, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : NewMemberMsg -> Model -> (NewMemberModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.newMemberModel
  in case msg of

    UpdateFirstName newVal ->
      ({sceneModel | firstName = newVal}, Cmd.none)

    UpdateLastName newVal ->
      ({sceneModel | lastName = newVal}, Cmd.none)

    UpdateEmail newVal ->
      ({sceneModel | email = newVal}, Cmd.none)

    ToggleIsAdult ->
      ({sceneModel | isAdult = not sceneModel.isAdult}, Cmd.none)

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : Model -> Html Msg
view kioskModel =
  let sceneModel = kioskModel.newMemberModel
  in genericScene kioskModel
    "Let's Create an Account!"
    "Please tell us about yourself:"
    ( div []
        [ sceneTextField kioskModel 2 "Your first name" sceneModel.firstName (NewMemberVector << UpdateFirstName)
        , vspace 0
        , sceneTextField kioskModel 3 "Your last name" sceneModel.lastName (NewMemberVector << UpdateLastName)
        , vspace 0
        , sceneEmailField kioskModel 4 "Your email address" sceneModel.email (NewMemberVector << UpdateEmail)
        , vspace 30
        , sceneCheckbox kioskModel 5 "Check if you are 18 or older!" sceneModel.isAdult (NewMemberVector ToggleIsAdult)
        ]
    )
    [ButtonSpec "OK" (Push NewUser)]

