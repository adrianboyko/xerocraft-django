
module ReceptionKiosk.NewUserScene exposing (init, view, update, NewUserModel)

-- Standard
import Html exposing (Html, div)
import Http

-- Third Party

-- Local
import ReceptionKiosk.Types exposing (..)
import ReceptionKiosk.SceneUtils exposing (..)
import ReceptionKiosk.Backend as Backend

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias NewUserModel =
  { userName: String
  , password1: String
  , password2: String
  , badNews: List String
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a = (SceneUtilModel {a | newUserModel : NewUserModel})

init : Flags -> (NewUserModel, Cmd Msg)
init flags =
  let sceneModel =
    { userName = ""
    , password1 = ""
    , password2 = ""
    , badNews = []
    }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : NewUserMsg -> KioskModel a -> (NewUserModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.newUserModel
  in case msg of

    UpdateUserName newVal ->
      let djangoizedVal = Backend.djangoizeId newVal
      in ({sceneModel | userName = djangoizedVal}, Cmd.none)

    UpdatePassword1 newVal ->
      ({sceneModel | password1 = newVal}, Cmd.none)

    UpdatePassword2 newVal ->
      ({sceneModel | password2 = newVal}, Cmd.none)

    ValidateUserNameAndPw ->
      validateUserIdAndPw kioskModel

    ValidateUserNameUnique result ->
      validateUserNameUnique kioskModel result

validateUserIdAndPw : KioskModel a -> (NewUserModel, Cmd Msg)
validateUserIdAndPw kioskModel =
  let
    sceneModel = kioskModel.newUserModel
    pwMismatch = sceneModel.password1 /= sceneModel.password2
    pwShort = String.length sceneModel.password1 < 6
    userNameShort = String.length sceneModel.userName < 4
    userNameLong = String.length sceneModel.userName > 20
    msgs = List.concat
      [ if pwMismatch then ["The password fields don't match"] else []
      , if pwShort then ["The password must have at least 6 characters."] else []
      , if userNameShort then ["The login id must have at least 4 characters."] else []
      , if userNameLong then ["The login id cannot be more than 20 characters."] else []
      ]
    getMatchingAccts = Backend.getMatchingAccts kioskModel.flags
    cmd = if List.length msgs > 0
      then Cmd.none
      else getMatchingAccts sceneModel.userName (NewUserVector << ValidateUserNameUnique)
  in
    ({sceneModel | badNews = msgs}, cmd)

validateUserNameUnique: KioskModel a -> Result Http.Error Backend.MatchingAcctInfo -> (NewUserModel, Cmd Msg)
validateUserNameUnique kioskModel result =
  let sceneModel = kioskModel.newUserModel
  in case result of
    Ok {target, matches} ->
      let
        matchingNames = List.map (\x -> String.toLower x.userName) matches
        chosenName = String.toLower sceneModel.userName
      in
        if List.member chosenName matchingNames then
          ({sceneModel | badNews = ["That user name is already in use."]}, Cmd.none)
        else
          ({sceneModel | badNews = []}, send (Push Waiver))
    Err error ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let sceneModel = kioskModel.newUserModel
  in genericScene kioskModel
    "Account Details"
    "Provide an id and password for our website:"
    ( div []
        [ sceneTextField kioskModel 6 "Choose a login id" sceneModel.userName (NewUserVector << UpdateUserName)
        , vspace 0
        , scenePasswordField kioskModel 7 "Choose a password" sceneModel.password1 (NewUserVector << UpdatePassword1)
        , vspace 0
        , scenePasswordField kioskModel 8 "Type password again" sceneModel.password2 (NewUserVector << UpdatePassword2)
        , vspace 30
        , formatBadNews sceneModel.badNews
        ]
    )
    [ButtonSpec "OK" (NewUserVector ValidateUserNameAndPw)]
