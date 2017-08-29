
module ReceptionKiosk.HowDidYouHearScene exposing (init, update, view, HowDidYouHearModel)

-- Standard
import Html exposing (Html, text)
import Http
import List.Extra

-- Third Party
import Material.Toggles as Toggles
import Material.Options as Options exposing (css)
import Material.List as Lists

-- Local
import ReceptionKiosk.Types exposing (..)
import ReceptionKiosk.SceneUtils exposing (..)
import ReceptionKiosk.Backend as Backend

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------


type alias HowDidYouHearModel =
  { discoveryMethods : List Backend.DiscoveryMethod  -- Fetched from backend
  , badNews : List String
  }

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a = (SceneUtilModel {a | howDidYouHearModel : HowDidYouHearModel})

init : Flags -> (HowDidYouHearModel, Cmd Msg)
init flags =
  let
    sceneModel = { discoveryMethods=[], badNews=[] }
    getDiscoveryMethods = Backend.getDiscoveryMethods flags
    request = getDiscoveryMethods (HowDidYouHearVector << AccDiscoveryMethods)
  in
    (sceneModel, request)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : HowDidYouHearMsg -> KioskModel a -> (HowDidYouHearModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.howDidYouHearModel
  in case msg of

    AccDiscoveryMethods (Ok {count, next, previous, results}) ->
      -- Data from backend might be paged, so we need to accumulate the batches as they come.
      let
        newMethods = sceneModel.discoveryMethods ++ results
        -- TODO: Need to get next batch if next is not Nothing.
      in
        ({sceneModel | discoveryMethods = newMethods}, Cmd.none)

    AccDiscoveryMethods (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

    ToggleDiscoveryMethod dm ->
      let
        replace = List.Extra.replaceIf
        picker = \x -> x.id == dm.id
        newDm = { dm | selected = not dm.selected }
      in
        -- TODO: This should also add/remove the discovery method choice on the backend.
        ({sceneModel | discoveryMethods = replace picker newDm sceneModel.discoveryMethods}, Cmd.none)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  genericScene kioskModel
    "Just Wondering"
    "How did you hear about us?"
    (howDidYouHearChoices kioskModel)
    [ButtonSpec "OK" (WizardVector <| Push <| NewMember)]

howDidYouHearChoices : KioskModel a -> Html Msg
howDidYouHearChoices kioskModel =
  let sceneModel = kioskModel.howDidYouHearModel
  in Lists.ul howDidYouHearCss
    (List.map
      ( \dm ->
          Lists.li [css "font-size" "18pt"]
            [ Lists.content [] [ text dm.name ]
            , Lists.content2 []
              [ Toggles.checkbox MdlVector [1000+dm.id] kioskModel.mdl  -- 1000 establishes an id range for these.
                  [ Toggles.value dm.selected
                  , Options.onToggle (HowDidYouHearVector <| ToggleDiscoveryMethod <| dm)
                  ]
                  []
              ]
            ]
      )
      sceneModel.discoveryMethods
    )


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

howDidYouHearCss =
  [ css "width" "400px"
  , css "margin-left" "auto"
  , css "margin-right" "auto"
  , css "margin-top" "80px"
  ]
