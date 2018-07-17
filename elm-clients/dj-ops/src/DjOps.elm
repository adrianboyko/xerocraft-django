module DjOps exposing (..)

-- Standard
import Html exposing (Html, div, text, select, option, input, p, br, span)
import Html as Html
import Html.Attributes exposing (style, href, attribute)
import Html.Events exposing (onClick, on)
import Http as Http
import Time exposing (Time, second)
import Date exposing (Date)

-- Third Party
import Material
import Material.Button as Button
import Material.Textfield as Textfield
import Material.Table as Table
import Material.Options exposing (css)
import Material.Icon as Icon
import Material.Layout as Layout
import Material.Color as Color
import Material.Footer as Footer
import DatePicker

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
  , selectedTab : Int
  , shows : List XisApi.Show
  , showDate : Maybe Date
  , datePicker : DatePicker.DatePicker
  }


init : Flags -> ( Model, Cmd Msg )
init flags =
  let
    auth = case flags.csrfToken of
      Just csrf -> DRF.LoggedIn csrf
      Nothing -> DRF.NoAuthorization
    getShowsCmd = model.xis.listShows ShowList_Result
    (datePicker, datePickerCmd ) = DatePicker.init
    model =
      { mdl = Material.model
      , xis = XisApi.createSession flags.xisRestFlags auth
      , time = 0
      , selectedTab = 0
      , shows = []
      , showDate = Nothing
      , datePicker = datePicker
      }
  in
    (model, Cmd.batch [getShowsCmd, Cmd.map SetDatePicker datePickerCmd])


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------


type
  Msg
  = Tick Time
  | Mdl (Material.Msg Msg)
  | ShowList_Result (Result Http.Error (DRF.PageOf XisApi.Show))
  | SelectTab Int
  | SetDatePicker DatePicker.Msg


update : Msg -> Model -> ( Model, Cmd Msg )
update action model =
  let xis = model.xis
  in case action of

    Mdl msg_ ->
      Material.update Mdl msg_ model

    SelectTab k ->
      ( { model | selectedTab = k }, Cmd.none )

    Tick newTime ->
      let
        seconds = (round newTime) // 1000
        newModel = { model | time = newTime }
      in
        ( newModel, Cmd.none )

    ShowList_Result (Ok {results}) ->
      ({model | shows=results}, Cmd.none)

    ShowList_Result (Err error) ->
      (model, Cmd.none)

    SetDatePicker msg ->
      let
        (newDatePicker, datePickerCmd, dateEvent) =
          DatePicker.update DatePicker.defaultSettings msg model.datePicker
        date = case dateEvent of
          DatePicker.NoChange -> model.showDate
          DatePicker.Changed newDate -> newDate
      in
        ( { model | showDate = date, datePicker = newDatePicker}
        , Cmd.map SetDatePicker datePickerCmd
        )


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

tabs model =
  (
    [ text "start"
    , text "tracks"
    , text "underwriting"
    , text "membership"
    ]
  , [ Color.background (Color.color Color.DeepPurple Color.S400) ]
  )

view : Model -> Html Msg
view model =
  Layout.render Mdl model.mdl
  [ Layout.fixedHeader
  , Layout.onSelectTab SelectTab
  ]
  { header = layout_header model
  , drawer = []
  , tabs = tabs model
  , main = [layout_main model]
  }

tagattr x = attribute x x

showSelector : Model -> Html Msg
showSelector model =
  select [style ["margin-left"=>"20px"], attribute "required" ""] <|
    ( option
       [attribute "value" "", tagattr "selected", tagattr "disabled", tagattr "hidden"]
       [text "Please pick a show..."]
    )

    ::
    (
      List.map
        (.data >> .title >> text >> List.singleton >> option [])
        model.shows
    )


showDateSelector : Model -> Html Msg
showDateSelector model =
  div [style ["margin-left"=>"20px"]]
  [ (DatePicker.view
      model.showDate
      DatePicker.defaultSettings
      model.datePicker
    ) |> Html.map SetDatePicker
  ]


layout_header : Model -> List (Html Msg)
layout_header model =
  [ Layout.title [css "margin" "20px"]
    [ text "DJ Ops Console"
    ]
  ]


layout_main : Model -> Html Msg
layout_main model =
  case model.selectedTab of
    0 ->
      tab_start model
    1 ->
      tab_tracks model
    _ ->
      p [] [text <| "Tab " ++ toString model.selectedTab ++ " not yet implemented."]


tab_start model =

  div [style ["margin"=>"30px", "zoom"=>"1.3"]]
  [ p [] [text "Welcome to the DJ Ops Console!"]
  , p [] [text "Choose a show to work on: ", br [] [], showSelector model]
  , p [] [text "And specify the show date: ", showDateSelector model]
  ]


tab_tracks model =
  div []
  [ Table.table [css "margin" "20px"]
    [ Table.tbody []
      (List.map (tableRow model) (List.range 1 60))
    ]
  ]


tableRow : Model -> Int -> Html Msg
tableRow model r =
  let
    aTd s r c opts =
      Table.td restTdStyle
        [Textfield.render Mdl [r,c] model.mdl (opts++[Textfield.label s]) []]
  in
    Table.tr []
    [ Table.td firstTdStyle [text <| toString r]
    , aTd "Artist" r 1 []
    , aTd "Title" r 2 []
    , aTd "MM:SS" r 3 [css "width" "55px"]
    , Table.td firstTdStyle
      [ Button.render Mdl [r] model.mdl
        [ Button.fab
        , Button.plain
        -- , Options.onClick MyClickMsg
        ]
        [ Icon.i "play_arrow"]
      ]

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

userIdPwInputStyle =
  style
  [ "margin-left" => "50px"
  ]

firstTdStyle =
  [ css "border-style" "none"
  , css "color" "gray"
  , css "font-size" "26pt"
  , css "font-weight" "bold"
  ]

restTdStyle =
  [ css "border-style" "none"
  , css "padding-top" "0"
  ]
