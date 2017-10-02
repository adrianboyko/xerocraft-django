module OpsCalendar exposing (..)

import Html exposing (Html, Attribute, a, div, table, tr, td, th, text, span, button, br, p)
import Html as Html
import Html.Attributes exposing (style, href)
import Html.Events exposing (onClick, on)
import Http as Http
import Task
import String
import Time exposing (Time)
import Date exposing (Date)
import Date.Extra.Format exposing (isoString)
import List
import DynamicStyle exposing (hover, hover_)
import Mouse exposing (Position)
import Maybe exposing (withDefault)
import Time exposing (Time, second)
import Material
import Material.Button as Button
import Material.Icon as Icon
import Material.Options as Options exposing (css)
import Json.Decode exposing (maybe)
import Json.Decode as Dec
import Json.Encode as Enc
import TaskApi exposing (..)


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
    { restUrls : RestUrls
    , initials : CalendarPage
    , csrfToken : String
    }


type State
    = Normal
    | SwitchingMonth
    | OperatingOnTask


type alias Model =
    { time : Time
    , mdl : Material.Model
    , user : Maybe User
    , tasks : MonthOfTasks
    , year : Int
    , month : Int
    , csrfToken : String
    , restUrls : RestUrls
    , selectedTaskId : Maybe Int
    , state : State
    , mousePt :
        Position
        -- The current most position.
    , detailPt :
        Position
        -- Where the detail "popup" is positioned.
    , dragStartPt :
        Maybe Position
        -- Where drag began, if user is dragging.
    , errorStr : Maybe String
    , errorStr2 : Maybe String
    }


init : Flags -> ( Model, Cmd Msg )
init { restUrls, initials, csrfToken } =
    ( Model
        0
        Material.model
        initials.user
        initials.tasks
        initials.year
        initials.month
        csrfToken
        restUrls
        Nothing
        Normal
        (Position 0 0)
        (Position 0 0)
        Nothing
        Nothing
        Nothing
    , Cmd.none
    )



-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------


type
    Msg
    -- Calendar app messages
    = ToggleTaskDetail Int
    | PrevMonth
    | NextMonth
    | NewMonthResult (Result Http.Error CalendarPage)
    | MouseMove Position
    | DragStart Position
    | DragFinish Position
    | ClaimTask Int OpsTask
    | VerifyTask Int OpsTask
    | UnstaffTask Int OpsTask
    | ClaimOpResult (Result Http.Error String)
    | Tick Time
    | Mdl (Material.Msg Msg)



-- For elm-mdl


update : Msg -> Model -> ( Model, Cmd Msg )
update action model =
    case action of
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

        ClaimTask memberId opsTask ->
            case opsTask.usersClaimId of
                Just claimId ->
                    update (VerifyTask memberId opsTask) model

                Nothing ->
                    case opsTask.timeWindow of
                        Nothing ->
                            ( model, Cmd.none )

                        -- Should never get here.
                        Just { begin, duration } ->
                            let
                                claim =
                                    Claim opsTask.taskId memberId begin duration (Date.fromTime model.time)

                                creds =
                                    LoggedIn model.csrfToken

                                newModel =
                                    { model | state = OperatingOnTask }
                            in
                                ( newModel, createClaim creds model.restUrls claim ClaimOpResult )

        VerifyTask memberId opsTask ->
            case opsTask.usersClaimId of
                Nothing ->
                    ( model, Cmd.none )

                -- Should never get here.
                Just claimId ->
                    let
                        creds =
                            LoggedIn model.csrfToken

                        newModel =
                            { model | state = OperatingOnTask }

                        todayIso =
                            isoDateStrFromTime model.time

                        statusField =
                            ( "status", Enc.string "C" )

                        -- need this because ClaimTask uses VerifyTask
                        dateVerifiedField =
                            ( "date_verified", Enc.string todayIso )

                        updateFields =
                            [ statusField, dateVerifiedField ]
                    in
                        ( newModel, updateClaim creds model.restUrls claimId updateFields ClaimOpResult )

        UnstaffTask memberId opsTask ->
            case opsTask.usersClaimId of
                Nothing ->
                    ( model, Cmd.none )

                -- Should never get here.
                Just claimId ->
                    let
                        creds =
                            LoggedIn model.csrfToken

                        newModel =
                            { model | state = OperatingOnTask }

                        statusField =
                            ( "status", Enc.string "A" )

                        todayIso =
                            isoDateStrFromTime model.time

                        dateVerifiedField =
                            ( "date_verified", Enc.string todayIso )

                        updateFields =
                            [ statusField, dateVerifiedField ]
                    in
                        ( newModel, updateClaim creds model.restUrls claimId updateFields ClaimOpResult )

        ClaimOpResult (Ok responsStr) ->
            ( { model | errorStr = Nothing, errorStr2 = Nothing }, getNewMonth model 0 )

        ClaimOpResult (Err err) ->
            ( { model | errorStr = Just (httpErrToStr err) }, getNewMonth model 0 )

        PrevMonth ->
            ( { model | state = SwitchingMonth, selectedTaskId = Nothing }, getNewMonth model -1 )

        NextMonth ->
            ( { model | state = SwitchingMonth, selectedTaskId = Nothing }, getNewMonth model 1 )

        NewMonthResult (Ok fetched) ->
            let
                newModel =
                    { model | state = Normal, user = fetched.user, tasks = fetched.tasks, year = fetched.year, month = fetched.month }
            in
                ( newModel, Cmd.none )

        NewMonthResult (Err err) ->
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
                    ( newModel, getNewMonth newModel 0 )
                else
                    ( newModel, Cmd.none )


getNewMonth : Model -> Int -> Cmd Msg
getNewMonth model delta =
    let
        -- TODO: These should be passed in from Django, not hard-coded here.
        url =
            "/tasks/ops-calendar-json/" ++ toStr (year) ++ "-" ++ toStr (month) ++ "/"

        newMonth =
            model.month + delta

        year =
            case newMonth of
                13 -> model.year + 1
                0 -> model.year - 1
                _ -> model.year

        month =
            case newMonth of
                13 -> 1
                0 -> 12
                _ -> newMonth

    in
        getCalendarPage year month NewMonthResult



-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------


actionButton : Model -> OpsTask -> String -> Html Msg
actionButton model opsTask action =
    case model.user of
        Nothing ->
            text ""

        Just { memberId, name } ->
            let
                ( msg, buttonText ) =
                    case action of
                        "U" ->
                            ( UnstaffTask, "Unstaff" )

                        "S" ->
                            ( ClaimTask, "Staff It" )

                        "V" ->
                            ( VerifyTask, "Verify" )

                        _ ->
                            assertNever "Action can only be S, U, or V"

                clickMsg =
                    msg memberId opsTask
            in
                button [ detailButtonStyle, onClick clickMsg ] [ text buttonText ]


detailView : Model -> OpsTask -> Html Msg
detailView model ot =
    let
        dragStartPt_ =
            withDefault model.mousePt model.dragStartPt

        left =
            px (model.detailPt.x + (model.mousePt.x - dragStartPt_.x))

        top =
            px (model.detailPt.y + (model.mousePt.y - dragStartPt_.y))

        onMouseDown =
            on "mousedown" (Dec.map DragStart Mouse.position)

        window =
            case ot.timeWindow of
                Nothing ->
                    Debug.crash "Must not be 'Nothing' at this point"

                Just x ->
                    x
    in
        div [ taskDetailStyle, onMouseDown, style [ "left" => left, "top" => top ] ]
            [ p [ taskDetailParaStyle ]
                [ text (ot.shortDesc)
                , br [] []
                , text ((durationToString ForHuman window.duration) ++ " @ " ++ (clockTimeToStr window.begin))
                , br [] []
                , if List.length (ot.staffedBy) > 0 then
                    text ("Staffed by " ++ (String.join ", " ot.staffedBy))
                  else
                    text "Not yet staffed!"
                ]
            , p [ taskDetailParaStyle ] [ text ot.instructions ]
            , button [ detailButtonStyle, onClick (ToggleTaskDetail ot.taskId) ] [ text "Close" ]
            , span []
                (List.map (actionButton model ot) ot.possibleActions)
            ]


taskView : Model -> OpsTask -> Html Msg
taskView model ot =
    case ot.timeWindow of
        Nothing ->
            text ""

        Just { begin, duration } ->
            let
                selectedTask =
                    withDefault -1 model.selectedTaskId

                operatingOnTask =
                    model.state == OperatingOnTask && ot.taskId == selectedTask

                taskStr =
                    if operatingOnTask then
                        "Working..."
                    else
                        ot.shortDesc
            in
                div []
                    [ div (List.concat [ (taskNameStyle ot), [ onClick (ToggleTaskDetail ot.taskId) ] ]) [ text taskStr ]
                    , if (model.selectedTaskId == Just ot.taskId) then
                        detailView model ot
                      else
                        text ""
                    ]


dayView : Model -> DayOfTasks -> Html Msg
dayView model dayOfTasks =
    let
        monthStyle =
            case dayOfTasks.isInTargetMonth of
                False ->
                    dayOtherMonthStyle

                True ->
                    dayTargetMonthStyle

        colorStyle =
            case dayOfTasks.isToday of
                False ->
                    monthStyle

                True ->
                    dayTodayStyle
    in
        td [ tdStyle, colorStyle ]
            (List.concat
                [ [ div [ dayNumStyle ] [ text (toString dayOfTasks.dayOfMonth) ] ]
                , List.map (taskView model) dayOfTasks.tasks
                ]
            )


weekView : Model -> WeekOfTasks -> Html Msg
weekView model weekOfTasks =
    tr []
        (List.map (dayView model) weekOfTasks)


monthView : Model -> Html Msg
monthView model =
    let
        daysOfWeek =
            [ "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat" ]

        headify =
            \x -> (th [ thStyle ] [ text x ])
    in
        table [ tableStyle ]
            (List.concat
                [ [ tr [] (List.map headify daysOfWeek) ]
                , (List.map (weekView model) model.tasks)
                ]
            )


headerView : Model -> Html Msg
headerView model =
    if model.state == SwitchingMonth then
        oneByThreeTable (text "") (text "Working") (text "")
    else
        oneByThreeTable
            (Button.render Mdl
                [ 0 ]
                model.mdl
                ([ Button.fab, Options.onClick PrevMonth ] ++ navButtonCss)
                [ Icon.i "navigate_before" ]
            )
            (text (monthName (model.month - 1) ++ " " ++ (toStr model.year)))
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
        , case model.user of
            Nothing ->
                let
                    y =
                        toString (model.year)

                    m =
                        toString (model.month)

                    url =
                        "/login/?next=/tasks/ops-calendar-spa/" ++ y ++ "-" ++ m

                    -- TODO: Django should provide url.
                in
                    a [ href url ] [ text "Log In to Edit Schedule" ]

            Just { memberId, name } ->
                a [ href "/logout/" ] [ text ("Log Out " ++ name) ]
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


monthName : Int -> String
monthName x =
    case x of
        0 ->
            "January"

        1 ->
            "February"

        2 ->
            "March"

        3 ->
            "April"

        4 ->
            "May"

        5 ->
            "June"

        6 ->
            "July"

        7 ->
            "August"

        8 ->
            "September"

        9 ->
            "October"

        10 ->
            "November"

        11 ->
            "December"

        _ ->
            Debug.crash "Provide a value from 0 to 11, inclusive"


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


taskNameCss opsTask =
    [ "font-family" => "Roboto Condensed"
    , "font-size" => "1em"
    , "margin" => "0"
    , "overflow" => "hidden"
    , "white-space" => "nowrap"
    , "text-overflow" => "ellipsis"
    , "width" => "120px"
    , "cursor" => "pointer"
    , "color"
        => case opsTask.staffingStatus of
            "S" ->
                "green"

            "P" ->
                "#c68e17"

            "U" ->
                "red"

            _ ->
                "#000000"
    , "text-decoration"
        => if opsTask.taskStatus == "C" then
            "line-through"
           else
            "none"
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
