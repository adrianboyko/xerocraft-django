
module NewUserScene exposing (init, sceneWillAppear, update, view, NewUserModel)

-- Standard
import Html exposing (Html, div)
import Http
import Time exposing (Time)

-- Third Party

-- Local
import MembersApi as MembersApi
import XisRestApi as XisApi
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import NewMemberScene exposing (NewMemberModel)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------


-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  ( SceneUtilModel
    { a
    | newUserModel : NewUserModel
    , newMemberModel : NewMemberModel
    , membersApi : MembersApi.Session Msg
    }
  )

type alias NewUserModel =
  { userName : String
  , password1 : String
  , password2 : String
  , badNews : List String
  }


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
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (NewUserModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  if appearingScene == NewUser
    then
      (kioskModel.newUserModel, focusOnIndex idxUserName)
    else
      (kioskModel.newUserModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : NewUserMsg -> KioskModel a -> (NewUserModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.newUserModel
  in case msg of

    UpdateUserName newVal ->
      let djangoizedVal = XisApi.djangoizeId newVal
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
    memberModel = kioskModel.newMemberModel

    norm = String.trim >> String.toLower
    uname = norm sceneModel.userName
    fname = norm memberModel.firstName
    lname = norm memberModel.lastName

    pwMismatch = sceneModel.password1 /= sceneModel.password2
    pwShort = String.length sceneModel.password1 < 6
    userNameShort = String.length uname < 4
    userNameLong = String.length uname > 20
    userNameIsFName = fname == uname
    userNameIsLName = lname == uname

    msgs = List.concat
      [ if pwMismatch then ["The password fields don't match"] else []
      , if pwShort then ["The password must have at least 6 characters."] else []
      , if userNameShort then ["The login id must have at least 4 characters."] else []
      , if userNameLong then ["The login id cannot be more than 20 characters."] else []
      , if userNameIsFName then ["The login id cannot be just your first name."] else []
      , if userNameIsLName then ["The login id cannot be just your last name."] else []
      ]
    getMatchingAccts = kioskModel.membersApi.getMatchingAccts
    cmd = if List.length msgs > 0
      then Cmd.none
      else getMatchingAccts sceneModel.userName (NewUserVector << ValidateUserNameUnique)
  in
    ({sceneModel | badNews = msgs}, cmd)

validateUserNameUnique: KioskModel a -> Result Http.Error MembersApi.MatchingAcctInfo -> (NewUserModel, Cmd Msg)
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
          ({sceneModel | badNews = []}, segueTo Waiver)
    Err error ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)


-----------------------------------------------------------------------------
-- TICK (called each second)
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

idxNewUserScene = mdlIdBase NewUser
idxUserName = [idxNewUserScene, 1]
idxPassword1 = [idxNewUserScene, 2]
idxPassword2 = [idxNewUserScene, 3]

view : KioskModel a -> Html Msg
view kioskModel =
  let sceneModel = kioskModel.newUserModel
  in genericScene kioskModel
    "Login Details"
    "Choose an id and password for our website:"
    ( div []
        [ sceneTextField kioskModel idxUserName "Choose a login id" sceneModel.userName (NewUserVector << UpdateUserName)
        , vspace 0
        , scenePasswordField kioskModel idxPassword1 "Choose a password" sceneModel.password1 (NewUserVector << UpdatePassword1)
        , vspace 0
        , scenePasswordField kioskModel idxPassword2 "Type password again" sceneModel.password2 (NewUserVector << UpdatePassword2)
        , vspace 30
        ]
    )
    [ButtonSpec "OK" (NewUserVector ValidateUserNameAndPw) True]
    sceneModel.badNews
