
module ReceptionKiosk.NewUserScene exposing (init, view, update)

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

update : NewUserMsg -> Model -> (NewUserModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.newUserModel
  in case msg of

    UpdateUserName newVal ->
      ({sceneModel | userName = newVal}, Cmd.none)

    UpdatePassword1 newVal ->
      ({sceneModel | password1 = newVal}, Cmd.none)

    UpdatePassword2 newVal ->
      ({sceneModel | password2 = newVal}, Cmd.none)

    ValidateUserNameAndPw ->
      validateUserIdAndPw sceneModel

    ValidateUserNameUnique result ->
      validateUserNameUnique sceneModel result

validateUserIdAndPw : NewUserModel -> (NewUserModel, Cmd Msg)
validateUserIdAndPw sceneModel =
  let
    pwMismatch = sceneModel.password1 /= sceneModel.password2
    pwShort = String.length sceneModel.password1 < 6
    userNameShort = String.length sceneModel.userName < 4
    msgs = List.concat
      [ if pwMismatch then ["The password fields don't match"] else []
      , if pwShort then ["The password must have at least 6 characters."] else []
      , if userNameShort then ["The user name must have at least 4 characters."] else []
      ]
    cmd = if List.length msgs > 0
      then Cmd.none
      else Backend.getMatchingAccts sceneModel.userName (NewUserVector << ValidateUserNameUnique)
  in
    ({sceneModel | badNews = msgs}, cmd)

validateUserNameUnique: NewUserModel -> Result Http.Error Backend.MatchingAcctInfo -> (NewUserModel, Cmd Msg)
validateUserNameUnique sceneModel result =
  case result of
    Ok {target, matches} ->
      let
        matchingNames = List.map (\x -> String.toLower x.userName) matches
        chosenName = String.toLower sceneModel.userName
      in
        if List.member chosenName matchingNames then
          ({sceneModel | badNews = ["That user name is already in use."]}, Cmd.none)
        else
          ({sceneModel | badNews = []}, send (Push HowDidYouHear))
    Err error ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : Model -> Html Msg
view kioskModel =
  let sceneModel = kioskModel.newUserModel
  in genericScene kioskModel
    "Account Details"
    "Provide an id and password for your account:"
    ( div []
        [ sceneTextField kioskModel 6 "Choose a user name" sceneModel.userName (NewUserVector << UpdateUserName)
        , vspace 0
        , scenePasswordField kioskModel 7 "Choose a password" sceneModel.password1 (NewUserVector << UpdatePassword1)
        , vspace 0
        , scenePasswordField kioskModel 8 "Type password again" sceneModel.password2 (NewUserVector << UpdatePassword2)
        , vspace 30
        , formatBadNews sceneModel.badNews
        ]
    )
    [ButtonSpec "OK" (NewUserVector ValidateUserNameAndPw)]
