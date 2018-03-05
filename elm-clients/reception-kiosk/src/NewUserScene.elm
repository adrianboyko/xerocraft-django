
module NewUserScene exposing (init, sceneWillAppear, update, view, NewUserModel)

-- Standard
import Html exposing (Html, div)
import Http
import Time exposing (Time)

-- Third Party
import Material
import List.Nonempty exposing (Nonempty)

-- Local
import XisRestApi as XisApi exposing (Member)
import Wizard.SceneUtils exposing (..)
import Types exposing (..)

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
  , newUserModel : NewUserModel
  , xisSession : XisApi.Session Msg
  }

type alias NewUserModel =
  ------------- Req'd Args:
  { howDidYouHear : Maybe (List Int)  -- DiscoveryMethod PKs
  , fname : Maybe String
  , lname : Maybe String
  , email : Maybe String
  , adult : Maybe Bool
  ------------- Other State:
  , userName : String
  , password1 : String
  , password2 : String
  , badNews : List String
  }

args x =
  ( x.howDidYouHear
  , x.fname
  , x.lname
  , x.email
  , x.adult
  )

init : Flags -> (NewUserModel, Cmd Msg)
init flags =
  let sceneModel =
    ------------- Req'd Args:
    { howDidYouHear = Nothing
    , fname = Nothing
    , lname = Nothing
    , email = Nothing
    , adult = Nothing
    ------------- Other State:
    , userName = ""
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

    NU_Segue (hdyh, fname, lname, email, adult) ->
      ( { sceneModel
        | howDidYouHear = Just hdyh
        , fname = Just fname
        , lname = Just lname
        , email = Just email
        , adult = Just adult
        }
      , send <| WizardVector <| Push NewUser
      )

    UpdateUserName newVal ->
      let djangoizedVal = XisApi.djangoizeId newVal
      in ({sceneModel | userName = djangoizedVal}, Cmd.none)

    UpdatePassword1 newVal ->
      ({sceneModel | password1 = newVal}, Cmd.none)

    UpdatePassword2 newVal ->
      ({sceneModel | password2 = newVal}, Cmd.none)

    ValidateUserNameAndPw ->
      validateUserIdAndPw kioskModel

    ValidateUserNameUnique (Ok {results}) ->
      validateUserNameUnique kioskModel results

    ValidateUserNameUnique (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)


validateUserIdAndPw : KioskModel a -> (NewUserModel, Cmd Msg)
validateUserIdAndPw kioskModel =

  case args kioskModel.newUserModel of

    (Just _, Just fnameArg, Just lnameArg, Just _, Just _) ->

      let
        sceneModel = kioskModel.newUserModel
        xis = kioskModel.xisSession

        norm = String.trim >> String.toLower
        uname = norm sceneModel.userName
        fname = norm fnameArg
        lname = norm lnameArg

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

        cmd =
          if List.length msgs > 0 then
            Cmd.none
          else
            xis.listMembers
              [XisApi.UsernameEquals sceneModel.userName, XisApi.IsActive True]
              (NewUserVector << ValidateUserNameUnique)
      in
        ({sceneModel | badNews = msgs}, cmd)

    _ -> (kioskModel.newUserModel, send <| ErrorVector <| ERR_Segue missingArguments)


validateUserNameUnique: KioskModel a -> List Member -> (NewUserModel, Cmd Msg)
validateUserNameUnique kioskModel matches =
  let
    sceneModel = kioskModel.newUserModel
    matchingNames = List.map (\x -> String.toLower x.data.userName) matches
    chosenName = String.toLower sceneModel.userName
  in
    if List.member chosenName matchingNames then
      ({sceneModel | badNews = ["That user name is already in use."]}, Cmd.none)
    else
      case args sceneModel of

        (Just wdyh, Just fn, Just ln, Just email, Just adult) ->
          ( { sceneModel | badNews = []}
          , send
              <| WaiverVector
              <| WVR_Segue (wdyh, fn, ln, email, adult, sceneModel.userName, sceneModel.password1)
          )

        _ -> ({ sceneModel | badNews = []}, send <| ErrorVector <| ERR_Segue missingArguments)


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
