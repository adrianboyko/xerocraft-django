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
import Json.Decode exposing (maybe)
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
--import TaskApi exposing (..)
import DjangoRestFramework as DRF exposing (PageOf)
import XisRestApi as XisApi
import CalendarDate as CD exposing (CalendarDate)
import CalendarPage as CP exposing (CalendarPage, CalendarRow, CalendarSquare)


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
  { xisRestFlags : XisApi.XisRestFlags
  , year : Int
  , month : Int
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
  , member : Maybe XisApi.Member
  , mousePt : Position  -- The current mouse position.
  , selectedTaskId : Maybe Int
  , state : State
  , time : Time
  , xis : XisApi.Session Msg
  }


init : Flags -> ( Model, Cmd Msg )
init flags =
  let
    calPage = CP.calendarPage flags.year (CD.intToMonth flags.month)
    xis = (XisApi.createSession flags.xisRestFlags (DRF.Token "testkiosk"))
    model =
      { calendarPage = calPage
      , detailPt = Position 0 0
      , dragStartPt = Nothing
      , errorStr = Nothing
      , errorStr2 = Nothing
      , mdl = Material.model
      , member = Nothing
      , mousePt = Position 0 0
      , selectedTaskId = Nothing
      , state = Normal
      , time = 0
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
  = ToggleTaskDetail Int
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

    ToggleTaskDetail clickedTaskId ->
      let
        detailModel =
          { model
            | selectedTaskId = Just clickedTaskId
            , detailPt = Position (model.mousePt.x - 200) (model.mousePt.y + 12)
          }
      in
        case model.selectedTaskId of
          Nothing ->
            ( detailModel, Cmd.none )

          Just selectedTaskId_ ->
            if selectedTaskId_ == clickedTaskId then
              ( { model | selectedTaskId = Nothing }, Cmd.none )
            else
              ( detailModel, Cmd.none )

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
            updateClaimCmd = xis.replaceClaim claim ClaimOpResult
          in
            (newModel, updateClaimCmd)

    ClaimOpResult (Ok claim) ->
      -- TODO: Need to reload one square of the calendar.
      ( { model | errorStr = Nothing, errorStr2 = Nothing }, Cmd.none)

    ClaimOpResult (Err err) ->
      ( { model | errorStr = Just (httpErrToStr err) }, Cmd.none)

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

    calPage = CP.calendarPage year (CD.intToMonth month)

    cmdList =
      CP.mapToList
        (\sq -> model.xis.listTasks [XisApi.ScheduledDateEquals sq.calendarDate] (DayOfTasksResult sq.calendarDate))
        calPage

  in
    ({model | calendarPage=calPage}, Cmd.batch cmdList)



-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------


actionButton : Model -> XisApi.Task -> String -> Html Msg
actionButton model opsTask action =
  case model.member of
    Nothing ->
      text ""

    Just { id, data } ->
      let
        ( msg, buttonText ) =
          case action of
            "U" -> ( UnstaffTask, "Unstaff" )
            "S" -> ( ClaimTask, "Staff It" )
            "V" -> ( VerifyTask, "Verify" )
            _   -> assertNever "Action can only be S, U, or V"

        clickMsg =
          msg id opsTask
      in
        button [ detailButtonStyle, onClick clickMsg ] [ text buttonText ]


detailView : Model -> XisApi.Task -> Html Msg
detailView model t =
  let
    dragStartPt_ = withDefault model.mousePt model.dragStartPt
    left = px (model.detailPt.x + (model.mousePt.x - dragStartPt_.x))
    top = px (model.detailPt.y + (model.mousePt.y - dragStartPt_.y))
    onMouseDown = on "mousedown" (Dec.map DragStart Mouse.position)

    (start, duration) =
      case (t.data.workStartTime, t.data.workDuration) of
        (Just s, Just d) -> (s, d)
        (_, _) -> Debug.crash "Start and duration not available"
  in
    div [ taskDetailStyle, onMouseDown, style [ "left" => left, "top" => top ] ]
      [ p [ taskDetailParaStyle ]
        [ text (t.data.shortDesc)
        , br [] []
        , text ((toString duration) ++ " @ " ++ (toString start))
        , br [] []
        , if 99 > 0 then text ("Staffed by " ++ "TODO!") else text "Not yet staffed!"
        ]
      , p [ taskDetailParaStyle ] [ text t.data.instructions ]
      , button [ detailButtonStyle, onClick (ToggleTaskDetail t.id) ] [ text "Close" ]
      , span []
        [text "TODO!"] -- (List.map (actionButton model t) t.data.possibleActions)
      ]


taskView : Model -> XisApi.Task -> Html Msg
taskView model t =
  case (t.data.workStartTime, t.data.workDuration) of

    (Just begin, Just duration) ->
      let
        selectedTask =
          withDefault -1 model.selectedTaskId

        operatingOnTask =
          model.state == OperatingOnTask && t.id == selectedTask

        taskStr =
          if operatingOnTask then
            "Working..."
          else
            t.data.shortDesc
      in
        div []

          [ div ((taskNameStyle t) ++ [onClick (ToggleTaskDetail t.id)])
            [ text taskStr ]

          , if (model.selectedTaskId == Just t.id) then
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
    year = model.calendarPage.year
    month = model.calendarPage.month
    monthStyle =
      if squareCD.year == year && squareCD.month == month then
        dayTargetMonthStyle
      else
        dayOtherMonthStyle

    colorStyle =
      if True then monthStyle else monthStyle -- TODO: dayTodayStyle

  in
    td [ tdStyle, colorStyle ]
      (List.concat
        [ [ div [ dayNumStyle ] [ text (toString squareCD.day) ] ]
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
    headify = \x -> (th [ thStyle ] [ text x ])
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
  div []
    [ br [] []
    , case model.member of
      Nothing ->
        let
          y = toString (model.calendarPage.year)
          m = toString (model.calendarPage.month)
          url = "/login/?next=/tasks/ops-calendar-spa/" ++ y ++ "-" ++ m
          -- TODO: Django should provide url.
        in
          a [ href url ] [ text "Log In to Edit Schedule" ]

      Just m ->
        a [ href "/logout/" ] [ text ("Log Out " ++ m.data.friendlyName) ]
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
  div [ containerStyle, unselectable ]
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
-- JSON Decoder
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- UTILITIES
-----------------------------------------------------------------------------


isoDateStrFromTime : Time -> String
isoDateStrFromTime time =
  String.left 10 (isoString (Date.fromTime time))


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


(=>) =
  (,)


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
    r =
      "5px"
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
      ]


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
    , "height" => "90px"
    , "width" => "120px"
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


taskNameCss task =
  [ "font-family" => "Roboto Condensed"
  , "font-size" => "1em"
  , "margin" => "0"
  , "overflow" => "hidden"
  , "white-space" => "nowrap"
  , "text-overflow" => "ellipsis"
  , "width" => "120px"
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
    [ "background-color" => "#f0ffff"
      -- azure
    ]


detailButtonStyle =
  style
    [ "font-family" => "Roboto Condensed"
    , "font-size" => "1.2em"
    , "cursor" => "pointer"
    , "margin-right" => "10px"
    ]
