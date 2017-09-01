
module ReceptionKiosk.NewMemberScene exposing (init, update, view, NewMemberModel)

-- Standard
import Html exposing (..)
import Http
import Regex exposing (..)

-- Third Party
import String.Extra as SE
import Material.List as Lists
import Material.Toggles as Toggles
import Material.Options as Options exposing (css)


-- Local
import MembersApi as MembersApi
import ReceptionKiosk.Types exposing (..)
import ReceptionKiosk.SceneUtils exposing (..)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias NewMemberModel =
  { firstName : String
  , lastName : String
  , email : String
  , isAdult : Maybe Bool
  , userIds : List String
  , badNews : List String
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a = (SceneUtilModel {a | newMemberModel : NewMemberModel})

init : Flags -> (NewMemberModel, Cmd Msg)
init flags =
  let model =
   { firstName = ""
   , lastName = ""
   , email = ""
   , isAdult = Nothing
   , userIds = ["larry"]
   , badNews = []
   }
  in (model, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : NewMemberMsg -> KioskModel a -> (NewMemberModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.newMemberModel
  in case msg of

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

    ValidateEmailUnique (Ok {target, matches}) ->
      if List.length matches > 0 then
        let userIds = List.map .userName matches
        in ({sceneModel | userIds=userIds}, send (WizardVector <| Push <| EmailInUse))
      else
        (sceneModel, send (WizardVector <| Push <| NewUser))

    ValidateEmailUnique (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)


-----------------------------------------------------------------------------
-- VALIDATE
-----------------------------------------------------------------------------

validate : KioskModel a -> (NewMemberModel, Cmd Msg)
validate kioskModel =
  let
    sceneModel = kioskModel.newMemberModel

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
    getMatchingAccts = MembersApi.getMatchingAccts kioskModel.flags
    cmd = if List.length msgs > 0
      then Cmd.none
      else getMatchingAccts sceneModel.email (NewMemberVector << ValidateEmailUnique)

  in
    ({sceneModel | badNews = msgs}, cmd)

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

idUnder18 = 1
idOver18 = 2

view : KioskModel a -> Html Msg
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
        , vspace 0
        , ageChoice kioskModel
        , vspace (if List.length sceneModel.badNews > 0 then 40 else 0)
        , formatBadNews sceneModel.badNews
        ]
    )
    [ButtonSpec "OK" (NewMemberVector <| Validate)]


ageChoice : KioskModel a -> Html Msg
ageChoice kioskModel =
  let
    sceneModel = kioskModel.newMemberModel
    idBase = mdlIdBase NewMember
  in
    Lists.ul ageListCss
      [ (Lists.li ageListItemCss
          [ Lists.content [] [text "I'm aged 18 or older"]
          , Lists.content2 []
            [ Toggles.radio MdlVector [idBase+idOver18] kioskModel.mdl
                [ Toggles.value (Maybe.withDefault False sceneModel.isAdult)
                , Options.onToggle (NewMemberVector <| ToggleIsAdult <| False)
                ]
                []
            ]
          ]
        )
      , (Lists.li ageListItemCss
          [ Lists.content [] [text "I'm younger than 18"]
          , Lists.content2 []
            [ Toggles.radio MdlVector [idBase+idUnder18] kioskModel.mdl
                [ Toggles.value (
                    case sceneModel.isAdult of
                      Nothing -> False
                      Just x -> not x
                  )
                , Options.onToggle (NewMemberVector << ToggleIsAdult <| True)
                ]
                []
            ]
          ]
        )
      ]




-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

ageListCss =
  [ css "width" "335px"
  , css "margin-left" "auto"
  , css "margin-right" "auto"
  , css "margin-top" "80px"
  ]

ageListItemCss =
  [ css "font-size" "22pt"
  , css "padding" "0"
  ]

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
