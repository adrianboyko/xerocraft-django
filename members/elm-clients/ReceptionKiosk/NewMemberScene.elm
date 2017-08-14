
module ReceptionKiosk.NewMemberScene exposing (init, update, view)

-- Standard
import Html exposing (..)
import Http
import Regex exposing (..)

-- Third Party
import String.Extra as SE

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
   , badNews = []
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

    Validate ->
      validate sceneModel

-----------------------------------------------------------------------------
-- VALIDATE
-----------------------------------------------------------------------------

validate : NewMemberModel -> (NewMemberModel, Cmd Msg)
validate sceneModel =
  let
    fNameShort = String.length sceneModel.firstName == 0
    lNameShort = String.length sceneModel.lastName == 0
    emailInvalid = not (contains emailRegex sceneModel.email)
    msgs = List.concat
      [ if fNameShort then ["Please provide your first name."] else []
      , if lNameShort then ["Please provide your last name."] else []
      , if emailInvalid then ["Your email address is not valid."] else []
      ]
    cmd = if List.length msgs > 0
      then Cmd.none
      else send (Push NewUser)
  in
    ({sceneModel | badNews = msgs}, cmd)

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
        , vspace (if List.length sceneModel.badNews > 0 then 40 else 0)
        , formatBadNews sceneModel.badNews
        ]
    )
    [ButtonSpec "OK" (NewMemberVector Validate)]

-----------------------------------------------------------------------------
-- UTILITIES
-----------------------------------------------------------------------------

emailRegex : Regex
emailRegex =
  let
    echar = "[a-z0-9!#$%&'*+/=?^_`{|}~-]"  -- email part
    alnum = "[a-z0-9]"  -- alpha numeric
    dchar = "[a-z0-9-]"  -- domain part
    emailRegexStr = "^E+(?:\\.E+)*@(?:A(?:D*A)?\\.)+A(?:D*A)?$"
      |> SE.replace "E" echar
      |> SE.replace "A" alnum
      |> SE.replace "D" dchar
  in
    regex emailRegexStr
