
module HowDidYouHearScene exposing (init, sceneWillAppear, update, view, HowDidYouHearModel)

-- Standard
import Html exposing (Html, text, div, span)
import Html.Attributes exposing (style)
import Http
import Random
import List.Extra as ListX

-- Third Party
import Material.Toggles as Toggles
import Material.Options as Options exposing (css)
import Random.List

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
        sceneModel = kioskModel.howDidYouHearModel
        getDMs = kioskModel.xisSession.listDiscoveryMethods
        request = getDMs (HowDidYouHearVector << AccDiscoveryMethods)
      in
        ({sceneModel | discoveryMethods = []}, request)

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
      let
        accumulatedMethods = sceneModel.discoveryMethods ++ results
        -- TODO: Need to get next batch if next is not Nothing.
        -- TODO: Shuffle accumulated methods, but ideally ONLY when next is Nothing.
        shuffleGen = Random.List.shuffle accumulatedMethods
        cmd = Random.generate (HowDidYouHearVector << ShuffledDiscoveryMethods) shuffleGen
      in
        ({sceneModel | discoveryMethods = accumulatedMethods}, cmd)

    ShuffledDiscoveryMethods shuffledMethods ->
      -- Slightly rearrange shuffled list to keep "Other" at the end.
      let
        isOther dm = dm.name == "Other"
        other = ListX.find isOther shuffledMethods
        otherAtEnd =
          case other of
            Nothing -> shuffledMethods |> Debug.log "Couldn't find 'Other' in:"
            Just o -> ListX.remove o shuffledMethods ++ [o]
      in
        ({sceneModel | discoveryMethods = otherAtEnd}, Cmd.none)

    AccDiscoveryMethods (Err error) ->
      ({sceneModel | badNews = [toString error]}, Cmd.none)

    ToggleDiscoveryMethod dm ->
      let
        newSelectedMethodPks =
          if List.member dm.id sceneModel.selectedMethodPks then
            ListX.remove dm.id sceneModel.selectedMethodPks
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
