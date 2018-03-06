
module NewMemberScene exposing (init, sceneWillAppear, update, view, NewMemberModel)

-- Standard
import Html exposing (..)
import Http
import Regex exposing (..)
import Time exposing (Time)

-- Third Party
import String.Extra as StringX
import List.Nonempty exposing (Nonempty)
import Material
import Material.List as Lists
import Material.Toggles as Toggles
import Material.Options as Options exposing (css)

-- Local
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import XisRestApi as XisApi


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
  , newMemberModel : NewMemberModel
  , xisSession : XisApi.Session Msg
  }


type alias NewMemberModel =
  ------------- Req'd Args:
  { howDidYouHear : Maybe (List Int)  -- DiscoveryMethod PKs
  ------------- Other State:
  , firstName : String
  , lastName : String
  , email : String
  , isAdult : Maybe Bool
  , badNews : List String
  }

args x = ( x.howDidYouHear )

init : Flags -> (NewMemberModel, Cmd Msg)
init flags =
  let model =
   ------------- Req'd Args:
   { howDidYouHear = Nothing
   ------------- Other State:
   , firstName = ""
   , lastName = ""
   , email = ""
   , isAdult = Nothing
   , badNews = []
   }
  in (model, Cmd.none)


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (NewMemberModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  if appearingScene == NewMember
    then
      (kioskModel.newMemberModel, focusOnIndex idxFirstName)
    else
      (kioskModel.newMemberModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : NewMemberMsg -> KioskModel a -> (NewMemberModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.newMemberModel
  in case msg of

    NM_Segue hdyh ->
      ( { sceneModel | howDidYouHear = Just hdyh }
      , send <| WizardVector <| Push NewMember
      )

    UpdateFirstName newVal ->
      ({sceneModel | firstName = newVal}, Cmd.none)

    UpdateLastName newVal ->
      ({sceneModel | lastName = newVal}, Cmd.none)

    UpdateEmail newVal ->
      ({sceneModel | email = newVal}, Cmd.none)

    ToggleIsAdult def ->
      let newVal = Just <| not <| Maybe.withDefault def sceneModel.isAdult
      in ({sceneModel | isAdult = newVal}, Cmd.none)

    Validate ->
      validate kioskModel

    ValidateEmailUnique (Ok {count, results}) ->

      -- The provided email address is already in use, so segue to Email in Use scene.
      if count > 0 then
        (sceneModel, send <| EmailInUseVector <| EIU_Segue results)

      -- The provided email address is not in use, so segue to New User scene.
      else
        case (sceneModel.howDidYouHear, sceneModel.isAdult) of
          (Just hdyh, Just adult) ->
            ( sceneModel,
              send
                <| (NewUserVector << NU_Segue)
                     ( hdyh
                     , sceneModel.firstName
                     , sceneModel.lastName
                     , sceneModel.email
                     , adult
                     )
            )

          _ ->
            (sceneModel, send <| ErrorVector <| ERR_Segue missingArguments)

    ValidateEmailUnique (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)


-----------------------------------------------------------------------------
-- VALIDATE
-----------------------------------------------------------------------------

validate : KioskModel a -> (NewMemberModel, Cmd Msg)
validate kioskModel =
  let
    sceneModel = kioskModel.newMemberModel
    xis = kioskModel.xisSession

    norm = String.trim
    fname = norm sceneModel.firstName
    lname = norm sceneModel.lastName

    fNameShort = String.length fname == 0
    lNameShort = String.length lname == 0
    emailInvalid = String.toLower sceneModel.email |> contains emailRegex |> not
    noAge = sceneModel.isAdult == Nothing

    msgs = List.concat
      [ if fNameShort then ["Please provide your first name."] else []
      , if lNameShort then ["Please provide your last name."] else []
      , if emailInvalid then ["Your email address is not valid."] else []
      , if noAge then ["Please specify if you are adult/minor."] else []
      ]

    cmd =
      if List.length msgs > 0 then
        Cmd.none
      else
        xis.listMembers
          [XisApi.EmailEquals sceneModel.email, XisApi.IsActive True]
          (NewMemberVector << ValidateEmailUnique)
  in
    ({sceneModel | badNews = msgs}, cmd)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

idxNewMemberScene = mdlIdBase NewMember
idxUnder18 = [idxNewMemberScene, 1]
idxOver18 = [idxNewMemberScene, 2]
idxFirstName = [idxNewMemberScene, 3]
idxLastName = [idxNewMemberScene, 4]
idxEmail = [idxNewMemberScene, 5]

view : KioskModel a -> Html Msg
view kioskModel =
  let sceneModel = kioskModel.newMemberModel
  in genericScene kioskModel
    "Let's Create an Account!"
    "Please tell us about yourself:"
    ( div []
        [ sceneTextField kioskModel idxFirstName "Enter your first name here" sceneModel.firstName (NewMemberVector << UpdateFirstName)
        , vspace 0
        , sceneTextField kioskModel idxLastName "Enter your last name here" sceneModel.lastName (NewMemberVector << UpdateLastName)
        , vspace 0
        , sceneEmailField kioskModel idxEmail "Enter your email address here" sceneModel.email (NewMemberVector << UpdateEmail)
        , vspace 0
        , ageChoice kioskModel
        ]
    )
    [ButtonSpec "OK" (NewMemberVector <| Validate) True]
    sceneModel.badNews


ageChoice : KioskModel a -> Html Msg
ageChoice kioskModel =
  let
    sceneModel = kioskModel.newMemberModel
  in
    div []
      [ vspace 40
      , Toggles.radio MdlVector idxOver18 kioskModel.mdl
          [ Toggles.value (Maybe.withDefault False sceneModel.isAdult)
          , Options.onToggle (NewMemberVector <| ToggleIsAdult <| False)
          , option_NoTabIndex
          ]
          [text "I'm aged 18 or older"]
      , vspace 30
      , Toggles.radio MdlVector idxUnder18 kioskModel.mdl
          [ Toggles.value
              ( case sceneModel.isAdult of
                  Nothing -> False
                  Just x -> not x
              )
            , Options.onToggle (NewMemberVector << ToggleIsAdult <| True)
            , option_NoTabIndex
          ]
          [text "I'm younger than 18"]
      , vspace 10
      ]


-----------------------------------------------------------------------------
-- TICK (called each second)
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------


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
      |> StringX.replace "E" echar
      |> StringX.replace "A" alnum
      |> StringX.replace "D" dchar
  in
    regex emailRegexStr
