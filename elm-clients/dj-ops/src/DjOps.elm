module DjOps exposing (..)

-- Standard
import Html exposing (Html, div, text, select, option, input, p, br, span, table, tr, td, i)
import Html as Html
import Html.Attributes exposing (style, href, attribute)
import Html.Events exposing (onInput, on, on)
import Http as Http
import Time exposing (Time, second)
import Date exposing (Date)
import Regex
import Char
import Keyboard exposing (KeyCode)
import Set exposing (Set)
import Task exposing (Task)
import Process
import Array exposing (Array)
import Maybe exposing (Maybe(..), withDefault)
import List exposing (head, tail)

-- Third Party
import Material
import Material.Button as Button
import Material.Textfield as Textfield
import Material.Table as Table
import Material.Options as Opts exposing (css)
import Material.Icon as Icon
import Material.Layout as Layout
import Material.Color as Color
import Material.Footer as Footer
import Material.Badge as Badge
import DatePicker
import List.Nonempty as NonEmpty exposing (Nonempty)
import List.Extra as ListX
import Hex as Hex
import Dialog as Dialog
import Maybe.Extra as MaybeX exposing (isJust, isNothing)
import Update.Extra as UpdateX exposing (updateModel, addCmd)

-- Local
import ClockTime as CT
import Duration as Dur
import PointInTime as PiT exposing (PointInTime)
import CalendarDate as CD
import XisRestApi as XisApi
import DjangoRestFramework as DRF


-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------

startTabId = 0
tracksTabId = 1
underwritingTabId = 2
finishTabId = 3

-- For Start Tab
userIdFieldId = [startTabId, 1]
passwordFieldId = [startTabId, 2]
loginButtonId = [startTabId, 3]
beginBroadcastButtonId = [startTabId, 4]

-- For Tracks Tab
numTrackRows = 60


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

type TracksTabEntryColumn
  = ArtistColumn
  | TitleColumn
  | DurationColumn

trackTabEntryColumnId : TracksTabEntryColumn -> Int
trackTabEntryColumnId col =
  case col of
    ArtistColumn -> 1
    TitleColumn -> 2
    DurationColumn -> 3

type alias TracksTabEntry =
  { playListEntryId : Maybe Int
  , artist : String
  , title : String
  , duration : String
  , savedArtist : String
  , savedTitle : String
  , savedDuration : String
  }

newTracksTabEntry : Maybe Int -> String -> String -> String -> String -> String -> String -> TracksTabEntry
newTracksTabEntry id artist title duration sArtist sTitle sDuration =
  TracksTabEntry id artist title duration sArtist sTitle sDuration

blankTracksTabEntry : TracksTabEntry
blankTracksTabEntry =
  newTracksTabEntry Nothing "" "" "" "" "" ""

tracksTabEntryIsDirty : TracksTabEntry -> Bool
tracksTabEntryIsDirty tte =
    [tte.artist, tte.title, tte.duration] /= [tte.savedArtist, tte.savedTitle, tte.savedDuration]

tracksTabEntryColumnIsDirty : TracksTabEntry -> TracksTabEntryColumn -> Bool
tracksTabEntryColumnIsDirty tte col =
  case col of
    ArtistColumn -> tte.artist /= tte.savedArtist
    TitleColumn -> tte.title /= tte.savedTitle
    DurationColumn -> tte.duration /= tte.savedDuration

type alias Model =
  { errMsgs : List String
  , keyboardIdleTime : Int
  , mdl : Material.Model
  , xisFlags : XisApi.XisRestFlags
  , xis : XisApi.Session Msg
  , currTime : PointInTime
  , selectedTab : Int
  , shows : List XisApi.Show
  , selectedShow : Maybe XisApi.Show
  , selectedShowDate : Maybe Date
  , episode : Maybe XisApi.Episode  -- This is derived from selectedShow + selectedShowDate.
  , datePicker : DatePicker.DatePicker
  , member : Maybe XisApi.Member
  , nowPlaying : Maybe XisApi.NowPlaying
  --- Tracks Tab model:
  , tracksTabEntries : Array TracksTabEntry
  --- Credentials:
  , userid : Maybe String
  , password : Maybe String
  }


init : Flags -> ( Model, Cmd Msg )
init flags =
  let
    getShowsCmd = model.xis.listShows ShowList_Result
    nowPlayingCmd = model.xis.nowPlaying NowPlaying_Result
    (datePicker, datePickerCmd ) = DatePicker.init
    model =
      { errMsgs = []
      , keyboardIdleTime = 0
      , mdl = Material.model
      , xisFlags = flags.xisRestFlags
      , xis = XisApi.createSession flags.xisRestFlags DRF.NoAuthorization
      , currTime = 0
      , selectedTab = 0
      , shows = []
      , selectedShow = Nothing
      , selectedShowDate = Nothing
      , episode = Nothing
      , datePicker = datePicker
      , member = Nothing
      , nowPlaying = Nothing
      --- Tracks Tab model:
      , tracksTabEntries = Array.repeat numTrackRows blankTracksTabEntry
      --- Credentials:
      , userid = Nothing
      , password = Nothing
      }
  in
    ( model
    , Cmd.batch
      [ getShowsCmd
      , nowPlayingCmd
      , Cmd.map SetDatePicker datePickerCmd
      , Layout.sub0 Mdl
      ]
    )


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------


type
  Msg
  = AcknowledgeDialog
  | Authenticate_Result (Result Http.Error XisApi.AuthenticationResult)
  | BeginBroadcast_Clicked
  | BroadcastCheckInUpdate_Result (Result Http.Error XisApi.Broadcast)
  | CheckNowPlaying
  | EpisodeCreate_Result XisApi.Show Date (Result Http.Error XisApi.Episode)
  | EpisodeList_Result XisApi.Show Date (Result Http.Error (DRF.PageOf XisApi.Episode))
  | EpisodeTrackDelete_Result Int (Result Http.Error String)
  | EpisodeTrackUpsert_Result (Result Http.Error XisApi.EpisodeTrack)
  | FetchTracksTabData
  | KeyDown KeyCode
  | KeyDown_Idle KeyCode
  | Login_Clicked
  | Mdl (Material.Msg Msg)
  | NowPlaying_Result (Result Http.Error XisApi.NowPlaying)
  | PasswordInput String
  | ShowList_Result (Result Http.Error (DRF.PageOf XisApi.Show))
  | ShowWasChosen String  -- ID of chosen show, as a String.
  | SelectTab Int
  | SetDatePicker DatePicker.Msg
  | Tick Time
  | Tick_Idle
  | Tick_NowPlaying
  | Tick_SaveTracksTab
  | TrackFieldUpdate Int TracksTabEntryColumn String  -- row, col, value
  | UseridInput String



update : Msg -> Model -> ( Model, Cmd Msg )
update action model =
  let xis = model.xis
  in case action of

    AcknowledgeDialog ->
      ( { model | errMsgs = [] }
      , Cmd.none
      )

    Authenticate_Result (Ok {isAuthentic, authenticatedMember}) ->
      if isAuthentic then
        let
          -- We just authenticated the userid & pw so they won't be Nothing.
          userid = withDefault "NO_ID" model.userid
          password = withDefault "NO_PW" model.password
          newModel =
            { model
            | member = authenticatedMember
            -- Need to create a new XIS session to change the authentication method to Basic.
            , xis = XisApi.createSession model.xisFlags (DRF.Basic userid password)
            }
        in
          (newModel, Cmd.none)
      else
        let
          errMsgs = ["Bad userid and/or password provided.", "Close this dialog and try again."]
          newModel = { model | member = Nothing, errMsgs = errMsgs }
        in
          (newModel, Cmd.none)

    BeginBroadcast_Clicked ->
      case model.episode of
        Just ep ->
          let
            bcData =
              { episode = model.xis.episodeUrl ep.id
              , date = CD.fromPointInTime model.currTime
              , hostCheckedIn = Just (CT.fromPointInTime model.currTime)
              , theType = "1ST"
              }
            createCmd = model.xis.createBroadcast bcData BroadcastCheckInUpdate_Result
          in
            (model, createCmd)
        Nothing ->
          let
            -- Should be impossible to get here because button can only be clicked if episode is set.
            dummy = Debug.log "ERR" "BeginBroadcast_Clicked"
          in
            (model, Cmd.none)

    BroadcastCheckInUpdate_Result (Ok broadcast) ->
      -- TODO: Record the broadcast?
      ( model, Cmd.none)

    CheckNowPlaying ->
      ( model
      , model.xis.nowPlaying NowPlaying_Result
      )

    FetchTracksTabData ->
      fetchTracksTabData model

    KeyDown code ->
      (model, Cmd.none)
        |> UpdateX.andThen update (KeyDown_Idle code)

    KeyDown_Idle code ->
      ( {model | keyboardIdleTime = 0 }, Cmd.none )

    Login_Clicked ->
      case (model.userid, model.password) of
        (Just id, Just pw) ->
          (model, model.xis.authenticate id pw Authenticate_Result)
        _ ->
          (model, Cmd.none)

    EpisodeTrackDelete_Result row (Ok s) ->
      let
        newTtes = Array.set row blankTracksTabEntry model.tracksTabEntries
      in
        ( { model | tracksTabEntries = newTtes }
        , Cmd.none
        )

    EpisodeTrackUpsert_Result (Ok et) ->
      case Array.get et.data.sequence model.tracksTabEntries of
        Just tte ->
          let
            newTte =
              { tte
              | playListEntryId = Just et.id
              , savedArtist = et.data.artist
              , savedTitle = et.data.title
              , savedDuration = et.data.duration
              }
            newTtes = Array.set et.data.sequence newTte model.tracksTabEntries
          in
            ( { model | tracksTabEntries = newTtes }
            , Cmd.none
            )
        Nothing ->
          let
            dummy = et |> Debug.log "Couldn't find row for"
          in
            (model, Cmd.none)

    Mdl msg_ ->
      Material.update Mdl msg_ model

    NowPlaying_Result (Ok np) ->
      let
        nowPlayingCmd = model.xis.nowPlaying NowPlaying_Result
        delaySeconds = case np.track of
          Just t ->
            let
              rs = t.remainingSeconds
            in
              if rs > 0 then rs * second
              else if rs < 1 && rs > -5 then 0.1 * second
              else 1 * second
          Nothing -> 1 * second
      in
        ( { model | nowPlaying = Just np }
        , delay delaySeconds CheckNowPlaying
        )

    PasswordInput s ->
      ({model | password = Just s}, Cmd.none)

    SelectTab k ->
      saveTracksTab
        { model | selectedTab = k }
        0  -- Save tracks tab IMMEDIATELY!

    SetDatePicker msg ->
      let
        (newDatePicker, datePickerCmd, dateEvent) =
          DatePicker.update DatePicker.defaultSettings msg model.datePicker
      in
        case dateEvent of
          DatePicker.NoChange ->
            ( { model | datePicker = newDatePicker }
            , Cmd.map SetDatePicker datePickerCmd
            )
          DatePicker.Changed d ->
            ( { model | selectedShowDate = d, datePicker = newDatePicker }
            , Cmd.map SetDatePicker datePickerCmd
            )
            |> UpdateX.andThen update FetchTracksTabData

    EpisodeCreate_Result selShow selShowDate (Ok episode) ->
      let
        msg = EpisodeList_Result selShow selShowDate <| Ok <| DRF.singletonPageOf episode
      in
        ( { model | episode = Just episode}, Cmd.none)
          |> UpdateX.andThen update msg

    EpisodeList_Result selShow selShowDate (Ok {count, results}) ->
      if count == 1 then
        let
          episode = head results
          tracksForTab = episode |> Maybe.map (.data >> .tracks) |> withDefault []
        in
          ({model | episode = episode }, Cmd.none)
            |> updateModel (populateTracksTabData tracksForTab)
      else if count == 0 then
        let
          selShowUrl = model.xis.showUrl selShow.id
          epData = XisApi.EpisodeData selShowUrl (CD.fromDate selShowDate) "" []
          tagger = EpisodeCreate_Result selShow selShowDate
          createCmd = model.xis.createEpisode epData tagger
        in
          (model, createCmd)
      else
        -- This should never happen because of "unique together" constraint in database.
        let
          dummy = results |> Debug.log ">1 Episode"
        in
          (model, Cmd.none)

    ShowList_Result (Ok {results}) ->
      ({model | shows=results}, Cmd.none)

    ShowList_Result (Err error) ->
      ({model | errMsgs=[toString error]}, Cmd.none)

    ShowWasChosen idStr ->
      case idStr |> String.toInt |> Result.toMaybe of
        Just id ->
          let
            show = ListX.find (\s->s.id==id) model.shows
          in
            ({ model | selectedShow = show}, Cmd.none)
              |> UpdateX.andThen update FetchTracksTabData
        Nothing ->
          let
            -- Should be impossible to get here since ids in question are integer PKs from database.
            dummy = idStr |> Debug.log "Couldn't convert to Int"
          in
            (model, Cmd.none)

    Tick newTime ->
      ({ model | currTime = newTime }, Cmd.none)
        |> UpdateX.andThen update Tick_NowPlaying
        |> UpdateX.andThen update Tick_Idle
        |> UpdateX.andThen update Tick_SaveTracksTab

    Tick_Idle ->
      ( { model | keyboardIdleTime = model.keyboardIdleTime + 1 }
      , Cmd.none
      )

    Tick_NowPlaying ->
      case model.nowPlaying of
        Just np ->
          case np.track of
            Just t ->
              let
                updatedTrack = {t | remainingSeconds = t.remainingSeconds - 1}
                updatedNowPlaying = {np | track = Just updatedTrack}
                updatedModel = {model | nowPlaying = Just updatedNowPlaying}
              in
                (updatedModel, Cmd.none)
            Nothing ->
                (model, Cmd.none)
        Nothing ->
          (model, Cmd.none)

    Tick_SaveTracksTab ->
      saveTracksTab model 5  -- Save tracks tab if keyboard has been idle for 5 seconds.

    TrackFieldUpdate row col val ->
      let
        tte1 = withDefault blankTracksTabEntry (Array.get row model.tracksTabEntries)
        tte2 =
          case col of
            ArtistColumn -> {tte1 | artist = val}
            TitleColumn -> {tte1 | title = val}
            DurationColumn -> {tte1 | duration = val}
        newModel = { model | tracksTabEntries = Array.set row tte2 model.tracksTabEntries}
      in
        (newModel, Cmd.none)

    UseridInput s ->
      ({model | userid = Just s}, Cmd.none)

    -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --

    Authenticate_Result (Err e) ->
      ({model | errMsgs=[toString e]}, Cmd.none)

    EpisodeTrackDelete_Result row (Err e) ->
      ({model | errMsgs=[toString e]}, Cmd.none)

    EpisodeTrackUpsert_Result (Err e) ->
      ({model | errMsgs=[toString e]}, Cmd.none)

    NowPlaying_Result (Err e) ->
      let
        dummy = toString e |> Debug.log "NowPlaying_Result"
      in
        ({model | nowPlaying = Nothing}, Cmd.none)

    BroadcastCheckInUpdate_Result  (Err e) ->
      ({model | errMsgs=[toString e]}, Cmd.none)

    EpisodeCreate_Result show date (Err e) ->
      let
        dummy = toString e |> Debug.log "EpisodeCreate_Result"
      in
        (model, Cmd.none)

    EpisodeList_Result show date (Err e) ->
      let
        dummy = toString e |> Debug.log "EpisodeList_Result"
      in
        (model, Cmd.none)


fetchTracksTabData : Model -> (Model, Cmd Msg)
fetchTracksTabData model =
  case (model.selectedShow, model.selectedShowDate) of

    (Just selShow, Just selShowDate) ->
      let
        showFilter = XisApi.EpisodeShowEquals selShow.id
        dateFilter = XisApi.EpisodeDateEquals <| CD.fromDate selShowDate
        tagger = EpisodeList_Result selShow selShowDate
        fetchCmd = model.xis.listEpisodes [showFilter, dateFilter] tagger
      in
        (model, fetchCmd)
    _ ->
      (model, Cmd.none)


populateTracksTabData : List XisApi.EpisodeTrack -> Model -> Model
populateTracksTabData ples model =
  let
    newModel = { model | tracksTabEntries = Array.repeat numTrackRows blankTracksTabEntry }
  in
    populateTracksTabData_Helper newModel ples


populateTracksTabData_Helper : Model -> List XisApi.EpisodeTrack -> Model
populateTracksTabData_Helper model plesRemaining =
  case plesRemaining of
    [] ->
      model
    ple::ples ->
      let
        seq = ple.data.sequence
        tte =
          newTracksTabEntry
            (Just ple.id)
            ple.data.artist ple.data.title ple.data.duration
            ple.data.artist ple.data.title ple.data.duration
        newModel = { model | tracksTabEntries = Array.set seq tte model.tracksTabEntries }
      in
        populateTracksTabData_Helper newModel ples


saveTracksTab : Model -> Int -> (Model, Cmd Msg)
saveTracksTab model minIdle =
  let
    reducer (row, tte) (model, cmd) =
      if tracksTabEntryIsDirty tte then
        let
          extraCmd =
            if List.all String.isEmpty [tte.artist, tte.title, tte.duration] then
              deleteEpisodeTrack model row tte
            else
              upsertEpisodeTrack model row tte
        in
          (model, cmd) |> addCmd extraCmd
      else
        -- Too soon after most recent change. Let's wait a bit more in case they're still typing.
        (model, cmd)
  in
    if model.keyboardIdleTime >= minIdle then
      List.foldl
        reducer
        (model, Cmd.none)
        (Array.toIndexedList model.tracksTabEntries)
    else
      (model, Cmd.none)


deleteEpisodeTrack : Model -> Int -> TracksTabEntry -> Cmd Msg
deleteEpisodeTrack model row tte =
  case tte.playListEntryId of
    Just id ->
      model.xis.deleteEpisodeTrackById id (EpisodeTrackDelete_Result row)
    Nothing ->
      -- Not yet saved, so nothing to delete.
      Cmd.none


upsertEpisodeTrack : Model -> Int -> TracksTabEntry -> Cmd Msg
upsertEpisodeTrack model row tte =
  case model.episode of
    Just episode ->
      let
        etData = XisApi.EpisodeTrackData
          (model.xis.episodeUrl episode.id) row tte.artist tte.title tte.duration
      in
        case tte.playListEntryId of
          Just idToUpdate ->
            model.xis.replaceEpisodeTrack
              (DRF.Resource idToUpdate etData)
              EpisodeTrackUpsert_Result
          Nothing ->
            model.xis.createEpisodeTrack
              etData
              EpisodeTrackUpsert_Result

    Nothing ->
      let
        dummy = (model.selectedShow, model.selectedShowDate) |> Debug.log "Episode is Nothing"
      in
        Cmd.none


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

tabs model =
  (
    [ text "start"
    , tracksTabTitle model
    , text "underwriting"
    , text "finish"
    ]
  , [ Color.background <| Color.color Color.DeepPurple Color.S400
    , Color.text <| Color.color Color.Green Color.S400
    ]
  )

tracksTabTitle : Model -> Html Msg
tracksTabTitle model =
  let
    filter = .playListEntryId >> isJust
    trackCount = model.tracksTabEntries |> Array.filter filter |> Array.length
  in
    if trackCount > 0 then
      Opts.span [Badge.add (toString trackCount)] [text "tracks"]
    else
      -- Margin-right, here, takes up same space as missing badge so that tab title spacing remains the same.
      span [style ["margin-right"=>"24px"]] [text "tracks"]


view : Model -> Html Msg
view model =
  div []
  [ Layout.render Mdl model.mdl
    [ Layout.fixedHeader
    , Layout.fixedTabs
    , Layout.onSelectTab SelectTab
    , Layout.selectedTab model.selectedTab
    ]
    { header = layout_header model
    , drawer = []
    , tabs = tabs model
    , main = [layout_main model]
    }
  , Dialog.view <| err_dialog_config model
  ]


err_dialog_config : Model -> Maybe (Dialog.Config Msg)
err_dialog_config model =

  if List.length model.errMsgs > 0 then
    Just
      { closeMessage = Just AcknowledgeDialog
      , containerClass = Nothing
      , containerId = Nothing
      , header = Just (text "😱 Error")
      , body = Just <| div [] <| List.map ((p [])<<List.singleton<<text) model.errMsgs
      , footer = Nothing
      }
  else
    Nothing

tagattr x = attribute x x


showSelector : Model -> Html Msg
showSelector model =
  select
    [ onInput ShowWasChosen
    , style ["margin-left"=>"0px"]
    , attribute "required" ""
    ]
    <|
    ( option
       [ attribute "value" ""
       , tagattr <| if isNothing model.selectedShow then "selected" else "dummy"
       , tagattr "disabled"
       , tagattr "hidden"
       ]
       [text "Please pick a show..."]
    )
    ::
    (
      List.map
        (\show ->
          option
            [ attribute "value" (toString show.id)
            , tagattr <| case model.selectedShow of
                Just s -> if show.id == s.id then "selected" else "dummy"
                Nothing -> "dummy"
            ]
            [text show.data.title]
        )
        model.shows
    )


showDateSelector : Model -> Html Msg
showDateSelector model =
  div [style ["margin-left"=>"0px"]]
  [ (DatePicker.view
      model.selectedShowDate
      DatePicker.defaultSettings
      model.datePicker
    ) |> Html.map SetDatePicker
  ]

layout_header : Model -> List (Html Msg)
layout_header model =
  [Layout.title []
  [ Layout.row []
    [ layout_header_col_appName model
    , layout_header_col_trackInfo model
    , layout_header_col_showInfo model
    ]
  ]
  ]


layout_header_col_appName : Model -> Html Msg
layout_header_col_appName model =
  div [style ["font-size"=>"20pt", "margin-right"=>"50px"]]
    [ span [style ["margin-right"=>"8px"]] [text "🎶 "]
    , text "DJ Ops"
    ]


timeRemaining min sec =
  let
    min0 = if String.length min < 2 then "0"++min else min
    sec0 = if String.length sec < 2 then "0"++sec else sec
    digitStyle = style
      [ "font-family"=>"'Share Tech Mono', monospace"
      , "letter-spacing"=>"-3px"
      ]
    colonStyle = style
      [ "margin-right"=>"-2px"
      , "margin-bottom"=>"3px"
      ]
  in
    div [style ["display"=>"inline-block", "vertical-align"=>"bottom", "padding-left"=>"3px", "padding-right"=>"3px", "margin-right"=>"10px", "font-size"=>"26pt", "border"=>"solid white 1px"]]
    [ span [digitStyle] [ text min0 ]
    , span [colonStyle] [ text ":" ]
    , span [digitStyle] [ text sec0 ]
    ]


stackedPair name1 val1 name2 val2 =
  let
    colonize s = text <| s ++ ": "
    italicize s = i [] [text s]
    theStyle = style
      [ "display"=>"inline-block"
      , "vertical-align"=>"bottom"
      , "font-size"=>"14pt"
      ]
  in
    div [theStyle]
    [ span [style ["margin-top"=>"4px"]]
      [ colonize name1, italicize val1
      , br [] []
      , colonize name2, italicize val2
      ]
    ]

dashes = "--"
dots = "..."

layout_header_col_trackInfo : Model -> Html Msg
layout_header_col_trackInfo model =
  let
    titleLabel = "Title"
    artistLabel = "Artist"
    blankInfo = [ timeRemaining dashes dashes, stackedPair titleLabel dots artistLabel dots]
    divStyle =
      style
      [ "width"=>"450px"
      , "white-space"=>"nowrap"
      , "overflow"=>"hidden"
      , "text-overflow"=>"ellipsis"
      , "margin-right"=>"50px"
      ]
  in div [divStyle]
    (
    case model.nowPlaying of
      Just {track} ->
        (
          case track of
            Just t ->
              if t.remainingSeconds > 0 then
                [ timeRemaining
                    (toString <| floor <| t.remainingSeconds/60)
                    (toString <| rem (floor t.remainingSeconds) 60)
                , stackedPair titleLabel t.title artistLabel t.artist
                ]
              else
                blankInfo

            Nothing ->
              blankInfo
        )

      Nothing ->
        blankInfo
    )

layout_header_col_showInfo : Model -> Html Msg
layout_header_col_showInfo model =
  let
    showLabel = "Show"
    hostLabel = "Host"
    blankInfo = [timeRemaining dashes dashes, stackedPair showLabel dots hostLabel dots]
  in div [style ["width"=>"450px", "white-space"=>"nowrap", "overflow"=>"hidden", "text-overflow"=>"ellipsis"]]
    (
    case model.nowPlaying of
      Just {show} ->
        (
          case show of
            Just s ->
              if s.remainingSeconds > 0 then
                [ timeRemaining
                    (toString <| floor <| s.remainingSeconds/60)
                    (toString <| rem (floor s.remainingSeconds) 60)
                , stackedPair showLabel s.title hostLabel (String.join " & " s.hosts)
                ]
              else
                blankInfo

            Nothing ->
              blankInfo
        )

      Nothing ->
        blankInfo
    )

layout_main : Model -> Html Msg
layout_main model =
  case model.selectedTab of
    0 ->
      tab_start model
    1 ->
      tab_tracks model
    _ ->
      p [] [text <| "Tab " ++ toString model.selectedTab ++ " not yet ietmented."]


tab_start : Model -> Html Msg
tab_start model =
  let
    numTd isSet = td [style ["padding-left"=>"5px", "font-size"=>"24pt", "color"=>(if isSet then "green" else "red")]]
    instTd = td [style ["padding-left"=>"15px"]]
    checkTd = td []
    para = p [style ["margin-top"=>"10px"]]
    row = tr []
    break = br [] []
  in
    div [style ["margin"=>"30px", "zoom"=>"1.3"]]
    [ p [] [text "Welcome to the DJ Ops Console!"]
    , table []
      [ row
        [ numTd (isJust model.userid && isJust model.password && isJust model.member) [text "❶ "]
        , instTd
          [ para
            [ input
                [ attribute "placeholder" "userid"
                , attribute "value" <| withDefault "" model.userid
                , onInput UseridInput
                ]
                []
            , break
            , input
                [ style ["margin-top"=>"3px"]
                , attribute "placeholder" "password"
                , attribute "type" "password"
                , attribute "value" <| withDefault "" model.password
                , onInput PasswordInput
                ]
                []
            , Button.render Mdl loginButtonId model.mdl
              [ css "position" "relative"
              , css "bottom" "20px"
              , css "margin-left" "10px"
              , Button.raised
              , Button.colored
              , Button.ripple
              , Opts.onClick Login_Clicked
              ]
              [ text "Login"]
            ]
          ]
        ]
      , row
        [ numTd (isJust model.selectedShow) [text "❷ "]
        , instTd [para [text "Choose a show to work on: ", br [] [], showSelector model]]
        ]
      , row
        [ numTd (isJust model.selectedShowDate) [text "❸ "]
        , instTd [para [text "Specify the show date: ", showDateSelector model]]
        ]
      , row
        [ numTd False [span [style ["color"=>"green"]] [text "❹ "]]
        , instTd
          [ para
            [ text "ONLY when it's time to start your LIVE show:"
            , br [] []
            , Button.render Mdl beginBroadcastButtonId model.mdl
              [ Button.raised
              , Button.colored
              , Button.ripple
              , if isNothing model.episode || isNothing model.member then
                  Button.disabled
                else case model.selectedShowDate of
                  Just ssd ->
                    if CD.fromDate ssd /= CD.fromTime model.currTime then Button.disabled else Opts.nop
                  Nothing ->
                    Button.disabled
              , Opts.onClick BeginBroadcast_Clicked
              ]
              [ text "Begin Broadcast!"]
            ]
          ]
        ]
      ]
    ]


tab_tracks : Model -> Html Msg
tab_tracks model =
  div []
    [ tracks_info model
    , tracks_table model
    ]


tracks_info : Model -> Html Msg
tracks_info model =
  div
    [ style
      [ "float"=>"right"
      , "position"=>"fixed"
      , "right"=>"50px"
      , "top"=>"150px"
      , "font-size"=>"16pt"
      ]
    ]
    [ p [style ["font-size"=>"16pt"]]
      ( case (model.selectedShow, model.selectedShowDate) of
        (Just show, Just date) ->
          [ text "⟵"
          , br [] []
          , text "Tracks for"
          , br [] []
          , text show.data.title
          , br [] []
          , text (date |> CD.fromDate |> CD.format "%a, %b %ddd")
          ]
        _ ->
          [ text "Finish the START tab."
          ]
      )
    ]

tracks_table : Model -> Html Msg
tracks_table model =
  Table.table [css "margin" "20px"]
    [ Table.tbody []
      (List.map (tracks_tableRow model) (List.range 1 numTrackRows))
    ]


tracks_tableRow : Model -> Int -> Html Msg
tracks_tableRow model r =
  let
    aTd s tte c opts =
      Table.td (restTdStyle++[css "color" (if tracksTabEntryColumnIsDirty tte c then "red" else "black")])
        [Textfield.render
          Mdl
          [tracksTabId, r, trackTabEntryColumnId c]  -- Textfield ID
          model.mdl
          ( opts
            ++
            [ Textfield.label s
            , Textfield.value <|
                case c of
                  ArtistColumn -> tte.artist
                  TitleColumn -> tte.title
                  DurationColumn -> tte.duration
            , if isJust model.member then Opts.nop else Textfield.disabled
            , Opts.onInput (TrackFieldUpdate r c)
            ]
          )
          []
        ]
  in
    case Array.get r model.tracksTabEntries of
      Just tte ->
        Table.tr [css "color" (if tracksTabEntryIsDirty tte then "red" else "black")]
        [ Table.td firstTdStyle [text <| toString r]
        , aTd "Artist" tte ArtistColumn []
        , aTd "Title" tte TitleColumn []
        , aTd "MM:SS" tte DurationColumn [css "width" "55px"]
        , Table.td firstTdStyle
          [ Button.render Mdl [tracksTabId, r] model.mdl
            [ Button.fab
            , Button.plain
            -- , Options.onClick MyClickMsg
            ]
            [ Icon.i "play_arrow"]
          ]
        ]
      Nothing ->
        let
          dummy = Debug.log <| "Couldn't get row."
        in
          Table.tr [] []


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------

subscriptions : Model -> Sub Msg
subscriptions model =
  Sub.batch
    [ Time.every second Tick
    , Keyboard.downs KeyDown
    , Layout.subs Mdl model.mdl
    ]


-----------------------------------------------------------------------------
-- UTILITIES
-----------------------------------------------------------------------------

-- From https://stackoverflow.com/questions/40599512/how-to-achieve-behavior-of-settimeout-in-elm
delay : Time.Time -> msg -> Cmd msg
delay time msg = Process.sleep time |> Task.perform (\_ -> msg)


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

-----------------------------------------------------------------------------
-- UTILITY
-----------------------------------------------------------------------------
