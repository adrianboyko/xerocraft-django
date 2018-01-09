module OpsCalendar exposing (..)


-- Standard
import Html exposing (Html, Attribute, a, div, table, tr, td, th, text, span, button, br, p)
import Html as Html
import Html.Attributes exposing (style, href)
import Html.Events exposing (onClick, on)
import Http as Http
import Task
import String
import Time exposing (Time)
import Date exposing (Date)
import List
import Mouse exposing (Position)
import Maybe exposing (withDefault)
import Time exposing (Time, second)
import Json.Decode as Dec
import Json.Encode as Enc

-- Third Party
import Date.Extra.Format exposing (isoString)
import DynamicStyle exposing (hover, hover_)
import Material
import Material.Button as Button
import Material.Icon as Icon
import Material.Options as Options exposing (css)

-- Local
import DjangoRestFramework as DRF exposing (PageOf)
import XisRestApi as XisApi
import CalendarDate as CD exposing (CalendarDate)
import CalendarPage as CP exposing (CalendarPage, CalendarRow, CalendarSquare)
import ClockTime as CT
import Duration as Dur


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
  , year : Int
  , month : Int
  , userName : Maybe String
  , memberId : Maybe Int
  }

type State
  = Normal
  | OperatingOnTask


type alias Model =
  { calendarPage : CalendarPage (List XisApi.Task)
  , detailPt : Position  -- Where the detail "popup" is positioned.
  , dragStartPt : Maybe Position  -- Where drag began, if user is dragging.
  , errorStr : Maybe String
  , errorStr2 : Maybe String
  , mdl : Material.Model
  , memberId : Maybe Int
  , mousePt : Position  -- The current mouse position.
  , selectedTask : Maybe XisApi.Task
  , state : State
  , time : Time
  , userName : Maybe String
  , xis : XisApi.Session Msg
  }


init : Flags -> ( Model, Cmd Msg )
init flags =
  let
    calPage = CP.calendarPage flags.year (CD.intToMonth flags.month)
    auth = case flags.csrfToken of
      Just csrf -> DRF.LoggedIn csrf
      Nothing -> DRF.NoAuthorization
    xis = XisApi.createSession flags.xisRestFlags auth
    model =
      { calendarPage = calPage
      , detailPt = Position 0 0
      , dragStartPt = Nothing
      , errorStr = Nothing
      , errorStr2 = Nothing
      , mdl = Material.model
      , memberId = flags.memberId
      , mousePt = Position 0 0
      , selectedTask = Nothing
      , state = Normal
      , time = 0
      , userName = flags.userName
      , xis = xis
      }
    cmds =
      CP.mapToList
        (\sq -> xis.listTasks [XisApi.ScheduledDateEquals sq.calendarDate] (DayOfTasksResult sq.calendarDate))
        calPage
  in
    (model, Cmd.batch cmds)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------


type
  Msg
  -- Calendar app messages
  = ToggleTaskDetail XisApi.Task
  | CloseTaskDetail Bool
  | PrevMonth
  | NextMonth
  | DayOfTasksResult CalendarDate (Result Http.Error (PageOf XisApi.Task))
  | MouseMove Position
  | DragStart Position
  | DragFinish Position
  | ClaimTask Int XisApi.Task
  | VerifyTask Int XisApi.Task
  | UnstaffTask Int XisApi.Task
  | ClaimOpResult (Result Http.Error XisApi.Claim)
  | Tick Time
  | Mdl (Material.Msg Msg)



-- For elm-mdl

update : Msg -> Model -> ( Model, Cmd Msg )
update action model =
  let xis = model.xis
  in case action of

    ToggleTaskDetail clickedTask ->
      let
        detailModel =
          { model
            | selectedTask = Just clickedTask
            , detailPt = Position (model.mousePt.x - 200) (model.mousePt.y + 12)
          }
      in
        case model.selectedTask of
          Nothing ->
            ( detailModel, Cmd.none )

          Just task ->
            if task.id == clickedTask.id then
              ( { model | selectedTask = Nothing }, Cmd.none )
            else
              ( detailModel, Cmd.none )

    CloseTaskDetail isDirectEvent ->
      if isDirectEvent then
        ({model | selectedTask = Nothing}, Cmd.none)
      else
        (model, Cmd.none)

    ClaimTask memberId task ->
      case xis.membersClaimOnTask memberId task of

        Just claim ->
          update (VerifyTask memberId task) model

        Nothing ->
          case (task.data.workStartTime, task.data.workDuration) of

            (begin, Just duration) ->
              let
                claimData =
                  XisApi.ClaimData
                    duration
                    begin
                    (xis.taskUrl task.id)
                    (xis.memberUrl memberId)
                    (Just (CD.fromTime model.time))
                    XisApi.CurrentClaimStatus
                    []  -- workSet

                createClaimCmd = xis.createClaim claimData ClaimOpResult
                newModel = { model | state=OperatingOnTask }
              in
                (newModel, createClaimCmd)

            (_, _) ->
              ( model, Cmd.none )

    VerifyTask memberId task ->
      case xis.membersClaimOnTask memberId task of

        Nothing ->
          ( model, Cmd.none )  -- Should never get here.

        Just claim ->
          let
            newModel = { model | state=OperatingOnTask }
            todayCD = model.time |> Date.fromTime |> CD.fromDate
            updatedClaim = claim
              |> XisApi.setClaimsStatus XisApi.CurrentClaimStatus
              |> XisApi.setClaimsDateVerified (Just todayCD)
            updateClaimCmd = xis.replaceClaim updatedClaim ClaimOpResult
          in
            (newModel, updateClaimCmd)

    UnstaffTask memberId task ->
      case xis.membersClaimOnTask memberId task of

        Nothing ->
          ( model, Cmd.none )

        -- Should never get here.
        Just claim ->
          let
            newModel = { model | state = OperatingOnTask }
            todayCD = model.time |> Date.fromTime |> CD.fromDate
            updatedClaim = claim
              |> XisApi.setClaimsStatus XisApi.AbandonedClaimStatus
              |> XisApi.setClaimsDateVerified (Just todayCD)
            updateClaimCmd = xis.replaceClaim updatedClaim ClaimOpResult
          in
            (newModel, updateClaimCmd)

    ClaimOpResult (Ok claim) ->
      let
        newModel = { model | state=Normal, errorStr=Nothing, errorStr2=Nothing }
        cmd = case model.selectedTask of
          Just t -> getTasksForDay model t.data.scheduledDate
          Nothing -> Cmd.none
      in
        (newModel, cmd)

    ClaimOpResult (Err err) ->
      let
        newModel = { model | state=Normal, errorStr=Just(httpErrToStr err) }
      in
        (newModel, Cmd.none)

    PrevMonth ->
      getNewMonth model -1

    NextMonth ->
      getNewMonth model 1

    DayOfTasksResult date (Ok {results}) ->
      let
        newCalPage = CP.update date (Just results) model.calendarPage
      in
      ( {model | calendarPage = newCalPage}, Cmd.none )

    DayOfTasksResult _ (Err err) ->
      ( { model | state = Normal, errorStr = Just (httpErrToStr err) }, Cmd.none )

    MouseMove newPt ->
      ( { model | mousePt = newPt }, Cmd.none )

    DragStart pt ->
      ( { model | dragStartPt = Just pt }, Cmd.none )

    DragFinish pt ->
      case model.dragStartPt of
        Nothing ->
          ( model, Cmd.none )

        Just { x, y } ->
          let
            newDetailPt =
              Position (model.detailPt.x + (pt.x - x)) (model.detailPt.y + (pt.y - y))
          in
            ( { model | dragStartPt = Nothing, detailPt = newDetailPt }, Cmd.none )

    Mdl msg_ ->
      Material.update Mdl msg_ model


    Tick newTime ->
      let
        seconds =
          (round newTime) // 1000

        newModel =
          { model | time = newTime }
      in
        if rem seconds 900 == 0 then
          getNewMonth newModel 0
        else
          ( newModel, Cmd.none )


getNewMonth : Model -> Int -> (Model, Cmd Msg)
getNewMonth model delta =
  let
    m = (CD.monthToInt model.calendarPage.month) + delta

    year =
      case m of
        13 -> model.calendarPage.year + 1
        0 -> model.calendarPage.year - 1
        _ -> model.calendarPage.year

    month =
      case m of
        13 -> 1
        0 -> 12
        _ -> m

    calPage =
      if delta == 0 then
        model.calendarPage
      else
        CP.calendarPage year (CD.intToMonth month)

    dates = CP.mapToList .calendarDate calPage
    cmdList = List.map (getTasksForDay model) dates

  in
    ({model | calendarPage=calPage}, Cmd.batch cmdList)


getTasksForDay : Model -> CalendarDate -> Cmd Msg
getTasksForDay model date =
  let
    filters = [XisApi.ScheduledDateEquals date]
    msger = (DayOfTasksResult date)
  in
    model.xis.listTasks filters msger



-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------


actionButton : Model -> Msg -> String -> Bool -> Html Msg
actionButton model clickMsg buttonText enabled =
  if not enabled then
    text ""
  else
    button [ detailButtonStyle, onClick clickMsg ] [ text buttonText ]


actionButtons : Model -> XisApi.Task -> List (Html Msg)
actionButtons model task =
  case model.memberId of
    Nothing ->
      [text "Log In to Edit"]
    Just m ->
      [ actionButton model (ClaimTask m task) "Staff It" (memberCanClaimTask model m task)
      , actionButton model (UnstaffTask m task) "Unstaff" (memberCanUnclaimTask model m task)
      , actionButton model (VerifyTask m task) "Verify" (memberCanVerifyTask model m task)
      ]


memberCanClaimTask : Model -> Int -> XisApi.Task -> Bool
memberCanClaimTask model memberId task =
  if model.xis.memberCanClaimTask memberId task then
    case (model.xis.membersClaimOnTask memberId task) of
      Just c ->
        c.data.status /= XisApi.CurrentClaimStatus
      Nothing ->
        True
  else
    False


memberCanUnclaimTask : Model -> Int -> XisApi.Task -> Bool
memberCanUnclaimTask model memberId task =
  case (model.xis.membersClaimOnTask memberId task) of
    Just c ->
      c.data.status == XisApi.CurrentClaimStatus
      && c.data.dateVerified /= Nothing
    Nothing ->
      False


memberCanVerifyTask : Model -> Int -> XisApi.Task -> Bool
memberCanVerifyTask model memberId task =
  case (model.xis.membersClaimOnTask memberId task) of
    Just c ->
      c.data.status == XisApi.CurrentClaimStatus
      && c.data.dateVerified == Nothing
    Nothing ->
      False


detailView : Model -> XisApi.Task -> Html Msg
detailView model t =
  let
    dragStartPt_ = withDefault model.mousePt model.dragStartPt
    left = px (model.detailPt.x + (model.mousePt.x - dragStartPt_.x))
    top = px (model.detailPt.y + (model.mousePt.y - dragStartPt_.y))
    onMouseDown = on "mousedown" (Dec.map DragStart Mouse.position)
    startStr = Maybe.map CT.toString t.data.workStartTime |> Maybe.withDefault "?"
    durStr = Maybe.map Dur.toString t.data.workDuration |> Maybe.withDefault "?"
    name = Maybe.withDefault "nobody" t.data.nameOfLikelyWorker
  in
    div [ taskDetailStyle, onMouseDown, style [ "left" => left, "top" => top ] ]
      (
        [ p [ taskDetailParaStyle ]
          [ text (t.data.shortDesc)
          , br [] []
          , text (durStr ++ " @ " ++ startStr)
          , br [] []
          , text ("Staffed by " ++ name)
          ]
        , p [ taskDetailParaStyle ] [ text t.data.instructions ]
        , button [ detailButtonStyle, onClick (ToggleTaskDetail t) ] [ text "Close" ]
        , span [] []
        ]
        ++
        actionButtons model t
      )


taskView : Model -> XisApi.Task -> Html Msg
taskView model t =
  case (t.data.workStartTime, t.data.workDuration) of

    (Just begin, Just duration) ->
      let
        selTask = model.selectedTask
        operatingOnTask = model.state == OperatingOnTask && Just t.id == Maybe.map .id selTask
        taskStr = if operatingOnTask then "Working..." else t.data.shortDesc
      in
        div []

          [ div ((taskNameStyle t) ++ [onClick (ToggleTaskDetail t)])
            [ text taskStr ]

          , if (Maybe.map .id selTask == Just t.id) then
              detailView model t
            else
              text ""
          ]

    (_, _) ->
      text ""


dayView : Model -> CalendarSquare (List XisApi.Task) -> Html Msg
dayView model square =
  let
    squareCD = square.calendarDate
    todayCD = CD.fromTime model.time
    year = model.calendarPage.year
    month = model.calendarPage.month
    monthStyle =
      if squareCD.year == year && squareCD.month == month then
        dayTargetMonthStyle
      else
        dayOtherMonthStyle

    colorStyle =
      if (CD.equal squareCD todayCD) then dayTodayStyle else monthStyle

  in
    td [ tdStyle, colorStyle, onClick2 CloseTaskDetail]
      (List.concat
        [ [ div [ dayNumStyle, onClick2 CloseTaskDetail ] [ text (toString squareCD.day) ] ]
        , case square.data of
            Just tasks -> List.map (taskView model) tasks
            Nothing -> [text "Working..."]
        ]
      )


weekView : Model -> CalendarRow (List XisApi.Task) -> Html Msg
weekView model row =
  tr []
    (List.map (dayView model) row)


monthView : Model -> Html Msg
monthView model =
  let
    page = model.calendarPage
    daysOfWeek = [ "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat" ]
    headify = \x -> (th [ thStyle, onClick2 CloseTaskDetail ] [ text x ])
  in
    table [ tableStyle ]
      (List.concat
        [ [ tr [] (List.map headify daysOfWeek) ]
        , (List.map (weekView model) model.calendarPage.rows)
        ]
      )


headerView : Model -> Html Msg
headerView model =
  oneByThreeTable

    (Button.render Mdl
      [ 0 ]
      model.mdl
      ([ Button.fab, Options.onClick PrevMonth ] ++ navButtonCss)
      [ Icon.i "navigate_before" ]
    )

    ( let cp = model.calendarPage
      in (text (String.concat [CD.monthName cp.month, " ", toStr cp.year]))
    )

    (Button.render Mdl
      [ 1 ]
      model.mdl
      ([ Button.fab, Options.onClick NextMonth ] ++ navButtonCss)
      [ Icon.i "navigate_next" ]
    )


loginView : Model -> Html Msg
loginView model =
  div [logInOutStyle]
    [ case model.userName of
      Nothing ->
        let
          y = model.calendarPage.year |> toString
          m = model.calendarPage.month |> CD.monthToInt |> toString
          url = "/login/?next=/tasks/ops-calendar-spa/" ++ y ++ "-" ++ m
          -- TODO: Django should provide url.
        in
          a [ href url ] [ text "Log In to Edit Schedule" ]

      Just userName ->
        a
          [ href "/logout/?next=/tasks/ops-calendar-spa/" ]
          [ text ("Log Out " ++ (String.toUpper userName)) ]
    ]


errorView : Model -> Html Msg
errorView model =
  let
    str =
      case model.errorStr of
        Nothing ->
          ""

        Just err ->
          err

    str2 =
      case model.errorStr2 of
        Nothing ->
          ""

        Just err ->
          err
  in
    div []
      [ text str
      , br [] []
      , text str2
      ]


view : Model -> Html Msg
view model =
  div [ containerStyle, unselectable, onClick2 CloseTaskDetail]
    [ headerView model
    , monthView model
    , loginView model
    , errorView model
    ]



-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------


subscriptions : Model -> Sub Msg
subscriptions model =
  Sub.batch
    [ Time.every second Tick
    , Mouse.moves MouseMove
    , Mouse.ups DragFinish
    ]


-----------------------------------------------------------------------------
-- CUSTOM EVENT HANDLERS
-----------------------------------------------------------------------------

isEventSource : Dec.Decoder Bool
isEventSource =
  let
    target = Dec.at ["target"] Dec.value
    currTarget = Dec.at ["currentTarget"] Dec.value
  in
    Dec.map2 (==) target currTarget


onClick2 : (Bool -> msg) -> Html.Attribute msg
onClick2 tagger =
  on "click" (Dec.map tagger isEventSource)


-----------------------------------------------------------------------------
-- UTILITIES
-----------------------------------------------------------------------------

httpErrToStr : Http.Error -> String
httpErrToStr err =
  case err of
    Http.Timeout ->
      "Timeout"

    Http.NetworkError ->
      "Network Error"

    Http.BadPayload errStr _ ->
      errStr

    Http.BadStatus response ->
      response.status.message

    Http.BadUrl errStr ->
      errStr



px : Int -> String
px number =
  toString number ++ "px"


toStr v =
  let
    str =
      toString v
  in
    if String.left 1 str == "\"" then
      String.dropRight 1 (String.dropLeft 1 str)
    else
      str


oneByThreeTable : Html Msg -> Html Msg -> Html Msg -> Html Msg
oneByThreeTable left center right =
  table [ navHeaderStyle ]
    -- TODO: Style should be a parameter
    [ tr []
      [ td [] [ left ]
      , td [] [ center ]
      , td [] [ right ]
      ]
    ]


assertNever : String -> a
assertNever str =
  Debug.crash str


assertNeverHandler : String -> a -> b
assertNeverHandler str =
  (\_ -> assertNever str)



-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------


(=>) = (,)

squareHeight = 90
squareWidth = 120

navButtonCss =
  [ css "margin" "0 10px"
  , css "padding" "5px"
  , css "min-width" "25px"
  , css "width" "25px"
  , css "height" "25px"
  ]


navHeaderStyle =
  style
    [ "font-family" => "Roboto Condensed, Arial, Helvetica"
    , "font-size" => "2em"
    , "height" => "35px"
    , "margin-left" => "auto"
    , "margin-right" => "auto"
    ]


taskDetailStyle =
  let
    r = "5px"
  in
    style
      [ "width" => "400px"
      , "background-color" => "#f0f0f0"
      , "position" => "absolute"
      , "text-align" => "left"
      , "padding" => "30px"
      , "border" => "1px solid black"
      , "border-radius" => r
      , "moz-border-radius" => r
      , "-webkit-border-radius" => r
      , "margin-right" => "auto"
      , "cursor" => "move"  -- fallback if grab cursor is unsupported
      , "cursor" => "grab"
      , "cursor" => "-moz-grab"
      , "cursor" => "-webkit-grab"
      ]

--taskDetailStyle:active {
--    cursor: grabbing;
--    cursor: -moz-grabbing;
--    cursor: -webkit-grabbing;
--}

taskDetailParaStyle =
  style
    [ "line-height" => "1.15"
    ]


unselectable =
  style
    [ "-moz-user-select" => "-moz-none"
    , "-khtml-user-select" => "none"
    , "-webkit-user-select" => "none"
    , "-ms-user-select" => "none"
    , "user-select" => "none"
    ]


containerStyle =
  style
    [ "padding" => "0 0"
    , "padding-top" => "3%"
    , "margin-top" => "0"
    , "width" => "100%"
    , "height" => "100%"
    , "text-align" => "center"
    , "font-family" => "Roboto Condensed, Arial, Helvetica"
    , "font-size" => "1em"
    ]


tableStyle =
  style
    [ "border-spacing" => "0"
    , "border-collapse" => "collapse"
    , "margin" => "0 auto"
    , "margin-top" => "2%"
    , "display" => "table"
    ]


buttonStyle =
  style
    [ "font-size" => "1.2em"
    , "margin" => "12px 7px"
      -- vert, horiz
    , "padding" => "7px 13px"
    ]


tdStyle =
  style
    [ "border" => "1px solid black"
    , "padding" => "10px"
    , "vertical-align" => "top"
    , "text-align" => "left"
    , "line-height" => "1.3"
    , "height" => px squareHeight
    , "width" => px squareWidth
    ]


thStyle =
  style
    [ "padding" => "5px"
    , "vertical-align" => "top"
    , "font-family" => "Arial, Helvetica"
    , "font-size" => "1.2em"
    , "font-weight" => "normal"
    ]


dayNumStyle =
  style
    [ "font-family" => "Arial, Helvetica"
    , "font-size" => "1.25em"
    , "margin-bottom" => "5px"
    ]

logInOutStyle =
  style
    [ "font-size" => "18pt"
    , "margin-top" => "30px"
    ]

taskNameCss task =
  [ "font-family" => "Roboto Condensed"
  , "font-size" => "1em"
  , "margin" => "0"
  , "overflow" => "hidden"
  , "white-space" => "nowrap"
  , "text-overflow" => "ellipsis"
  , "width" => px squareWidth
  , "cursor" => "pointer"
  , "color" => case task.data.staffingStatus of
      XisApi.SS_Staffed     -> "green"
      XisApi.SS_Provisional -> "#c68e17"
      XisApi.SS_Unstaffed   -> "red"
      _                     -> "#000000"
  , "text-decoration" => if task.data.status == "C" then "line-through" else "none"
  ]


taskNameStyle opsTask =
  hover_
    (taskNameCss opsTask)
    [ ( "background-color", "transparent", "#b3ff99" ) ]


-- rollover


dayOtherMonthStyle =
  style
    [ "background-color" => "#eeeeee"
    ]


dayTargetMonthStyle =
  style
    [ "background-color" => "white"
    ]


dayTodayStyle =
  style
    [ "background-color" => "#ffffcc" -- light yellow
    ]


detailButtonStyle =
  style
    [ "font-family" => "Roboto Condensed"
    , "font-size" => "1.2em"
    , "cursor" => "pointer"
    , "margin-right" => "10px"
    ]
