
module HowDidYouHearScene exposing (init, sceneWillAppear, update, view, HowDidYouHearModel)

-- Standard
import Html exposing (Html, text, div, span)
import Html.Attributes exposing (style)
import Http
import List.Extra

-- Third Party
import Material.Toggles as Toggles
import Material.Options as Options exposing (css)

-- Local
import MembersApi as MembersApi
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import XisRestApi as XisApi


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

type alias HowDidYouHearModel =
  { discoveryMethods : List MembersApi.DiscoveryMethod  -- Fetched from MembersApi
  , selectedMethodPks : List Int
  , badNews : List String
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  ( SceneUtilModel
    { a
    | howDidYouHearModel : HowDidYouHearModel
    , xisSession : XisApi.Session Msg
    }
  )


init : Flags -> (HowDidYouHearModel, Cmd Msg)
init flags =
  let
    sceneModel = { discoveryMethods=[], selectedMethodPks=[], badNews=[] }
  in
    (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (HowDidYouHearModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  case appearingScene of

    Welcome ->
      let
        getDMs = kioskModel.xisSession.getDiscoveryMethodList
        request = getDMs (HowDidYouHearVector << AccDiscoveryMethods)
      in
        (kioskModel.howDidYouHearModel, request)

    _ ->
      (kioskModel.howDidYouHearModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : HowDidYouHearMsg -> KioskModel a -> (HowDidYouHearModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.howDidYouHearModel
  in case msg of

    AccDiscoveryMethods (Ok {count, next, previous, results}) ->
      -- Data from MembersApi might be paged, so we need to accumulate the batches as they come.
      let
        newMethods = sceneModel.discoveryMethods ++ results
        -- TODO: Need to get next batch if next is not Nothing.
      in
        ({sceneModel | discoveryMethods = newMethods}, Cmd.none)

    AccDiscoveryMethods (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

    ToggleDiscoveryMethod dm ->
      let
        newSelectedMethodPks =
          if List.member dm.id sceneModel.selectedMethodPks then
            List.Extra.remove dm.id sceneModel.selectedMethodPks
          else
            dm.id :: sceneModel.selectedMethodPks
      in
        ({sceneModel | selectedMethodPks=newSelectedMethodPks}, Cmd.none)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let sceneModel = kioskModel.howDidYouHearModel
  in genericScene kioskModel
    "Just Wondering"
    "How did you hear about us?"
    (howDidYouHearChoices kioskModel)
    [ButtonSpec "OK" (WizardVector <| Push <| NewMember)]
    sceneModel.badNews

howDidYouHearChoices : KioskModel a -> Html Msg
howDidYouHearChoices kioskModel =
  let
    sceneModel = kioskModel.howDidYouHearModel
    visibleMethods = List.filter .visible sceneModel.discoveryMethods
    idBase = mdlIdBase HowDidYouHear
  in
    div [howDidYouHearStyle]
      ( [vspace 30] ++
        (List.map
          ( \dm ->
              span []
                [ Toggles.checkbox MdlVector [idBase+dm.id] kioskModel.mdl
                      [ Toggles.value (List.member dm.id sceneModel.selectedMethodPks)
                      , Options.onToggle (HowDidYouHearVector <| ToggleDiscoveryMethod <| dm)
                      ]
                      [text dm.name]
                , vspace 30
                ]
          )
          visibleMethods
        )
      )


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

howDidYouHearStyle = style
  [ "width" => "350px"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "padding-left" => "125px"
  , "text-align" => "left"
  ]
