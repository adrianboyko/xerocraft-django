module KmkrTrackLogger exposing (..)

-- Standard
import Html exposing (Html, div, text)
import Html as Html
import Html.Attributes exposing (style, href)
import Html.Events exposing (onClick, on)
import Http as Http
import Time exposing (Time, second)

-- Third Party
import Material
import Material.Button as Button

-- Local
import ClockTime as CT
import Duration as Dur
import PointInTime as PiT exposing (PointInTime)
import XisRestApi as XisApi
import DjangoRestFramework as DRF


-----------------------------------------------------------------------------
-- MAIN
-----------------------------------------------------------------------------

main =
  Html.programWithFlags
    { init = init
    , view = view
    , update = update
    , subscriptions = subscriptions
    }


-----------------------------------------------------------------------------
-- MODEL
-----------------------------------------------------------------------------

-- These are params from the server. Elm docs tend to call them "flags".

type alias Flags =
  { csrfToken : Maybe String
  , xisRestFlags : XisApi.XisRestFlags
  }


type alias Model =
  { mdl : Material.Model
  , xis : XisApi.Session Msg
  , time : PointInTime
  }


init : Flags -> ( Model, Cmd Msg )
init flags =
  let
    auth = case flags.csrfToken of
      Just csrf -> DRF.LoggedIn csrf
      Nothing -> DRF.NoAuthorization
    model =
      { mdl = Material.model
      , xis = XisApi.createSession flags.xisRestFlags auth
      , time = 0
      }
  in
    (model, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------


type
  Msg
  = Tick Time
  | Mdl (Material.Msg Msg)


update : Msg -> Model -> ( Model, Cmd Msg )
update action model =
  let xis = model.xis
  in case action of

    Mdl msg_ ->
      Material.update Mdl msg_ model

    Tick newTime ->
      let
        seconds = (round newTime) // 1000
        newModel = { model | time = newTime }
      in
        ( newModel, Cmd.none )



-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------


view : Model -> Html Msg
view model =
  div []
    [ text "Hello"
    ]



-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------


subscriptions : Model -> Sub Msg
subscriptions model =
  Sub.batch
    [ Time.every second Tick
    ]


-----------------------------------------------------------------------------
-- UTILITIES
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------


(=>) = (,)


unselectable =
  style
    [ "-moz-user-select" => "-moz-none"
    , "-khtml-user-select" => "none"
    , "-webkit-user-select" => "none"
    , "-ms-user-select" => "none"
    , "user-select" => "none"
    ]


