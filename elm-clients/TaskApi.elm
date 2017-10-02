module TaskApi
    exposing
        ( CalendarPage
        , Claim
        , createClaim
        , Credentials(LoggedIn, Token)
        , ClockTime
        , clockTimeToStr
        , Duration
        , durationFromString
        , durationToString
        , getCalendarPage
        , getCurrCalendarPage
        , getCurrCalendarPageForMember
        , TimeWindow
        , RestUrls
        , OpsTask
        , DayOfTasks
        , MonthOfTasks
        , WeekOfTasks
        , Target(ForHuman, ForRest)
        , updateClaim
        , User
        )

import Date exposing (Date)
import Date.Extra.Format exposing (isoString)
import Time exposing (Time, hour, minute, second)
import Json.Encode as Enc
import Json.Decode as Dec exposing (maybe)
import Json.Decode.Pipeline exposing (decode, required)
import Task exposing (Task)
import Regex exposing (Regex, regex, split)
import List
import Http
import String


type Target
    = ForHuman
    | ForRest

-- Remember: User has user/member/worker on server side, with userId!=memberId!=workerId, in general.
type alias User =
    { memberId : Int
    , name : String
    }

type alias OpsTask =
    { taskId : Int
    , isoDate : String
    , shortDesc : String
    , timeWindow : Maybe TimeWindow
    , instructions : String
    , staffingStatus : String
    , possibleActions : List String
    , staffedBy : List String  -- Friendly names
    , taskStatus : String
    , usersClaimId : Maybe Int
    }

type alias DayOfTasks =
    { dayOfMonth : Int
    , isInTargetMonth : Bool
    , isToday : Bool
    , tasks : List OpsTask
    }

type alias WeekOfTasks =
    List DayOfTasks

type alias MonthOfTasks =
    List WeekOfTasks

type alias CalendarPage =
    { user : Maybe User
    , tasks : MonthOfTasks
    , year : Int
    , month : Int
    }

-----------------------------------------------------------------------------
-- TIME WINDOW
-----------------------------------------------------------------------------


type alias RestUrls =
    { memberList : String
    , taskList : String
    , claimList : String
    }



-----------------------------------------------------------------------------
-- TIME WINDOW
-----------------------------------------------------------------------------


type alias TimeWindow =
    { begin : ClockTime
    , duration : Duration
    }


decodeTimeWindow : Dec.Decoder TimeWindow
decodeTimeWindow =
    Dec.map2 TimeWindow
        (Dec.field "begin" decodeClockTime)
        (Dec.field "duration" Dec.float)



-----------------------------------------------------------------------------
-- CLOCK TIME
-----------------------------------------------------------------------------


type alias ClockTime =
    { hour :
        Int
        -- Value must be 0 to 23, inclusive
    , minute :
        Int
        -- Value must be 0 to 59, inclusive
    }


decodeClockTime : Dec.Decoder ClockTime
decodeClockTime =
    Dec.map2 ClockTime
        (Dec.field "hour" Dec.int)
        (Dec.field "minute" Dec.int)


clockTimeToStr : ClockTime -> String
clockTimeToStr ct =
    let
        hour =
            String.padLeft 2 '0' (toString ct.hour)

        minute =
            String.padLeft 2 '0' (toString ct.minute)
    in
        hour ++ ":" ++ minute



-----------------------------------------------------------------------------
-- DURATION
-----------------------------------------------------------------------------


type alias Duration =
    Float -- A time duration in milliseconds, so we can use core Time's units.


durationFromString : String -> Duration
durationFromString s =
    let
        unResult =
            \x ->
                case x of
                    Ok val ->
                        val

                    Err str ->
                        Debug.crash str

        partsAsStrs =
            split Regex.All (regex "[: ]") s

        partsAsResults =
            List.map String.toFloat partsAsStrs

        partsAsFloats =
            List.map unResult partsAsResults

        weights3 =
            [ hour, minute, second ]

        weights4 =
            [ 24 * hour ] ++ weights3

        weights =
            if (List.length partsAsFloats) == 4 then
                weights4
            else
                weights3
    in
        List.foldr (+) 0 (List.map2 (*) weights partsAsFloats)



-- Python form for API (friendly = False): "[<days> ]<hours>:<minutes>:<seconds>"
-- User-friendly form (friendly = True): "3.5 hrs"


durationToString : Target -> Duration -> String
durationToString target dhms =
    let
        day =
            24.0 * hour

        days =
            dhms / day |> floor |> toFloat

        hms =
            dhms - (days * day)

        hours =
            hms / hour |> floor |> toFloat

        ms =
            hms - (hours * hour)

        minutes =
            ms / minute |> floor |> toFloat

        seconds =
            ms - (minutes * minute)

        pad =
            toString >> (String.padLeft 2 '0')
    in
        case target of
            ForHuman ->
                -- TODO: This is only good for tasks that are less than a day long, which suffices for now.
                toString (hours + minutes / 60.0) ++ " hrs"

            ForRest ->
                (toString days) ++ " " ++ (pad hours) ++ ":" ++ (pad minutes) ++ ":" ++ (pad seconds)



-----------------------------------------------------------------------------
-- CLAIM
-----------------------------------------------------------------------------


type alias Claim =
    { taskId : Int
    , claimantId :
        Int  -- Must be a member id, not a user id.
    , startOfClaim : ClockTime
    , durationOfClaim : Duration
    , verifiedOn : Date
    }


type Credentials
    = LoggedIn String  -- Use this if the user already has a logged in session. String is the csrfToken.
    | Token String


encodeBody : List ( String, Enc.Value ) -> Http.Body
encodeBody fields =
    fields
        |> Enc.object
        |> Http.jsonBody


makeClaimBody : Claim -> RestUrls -> Http.Body
makeClaimBody claim restUrls =
    let
        claimantIdStr =
            toString claim.claimantId

        taskIdStr =
            toString claim.taskId

        startOfClaimStr =
            (toString claim.startOfClaim.hour) ++ ":" ++ (toString claim.startOfClaim.minute) ++ ":00"

        durationOfClaimStr =
            durationToString ForRest claim.durationOfClaim

        verifiedOnStr =
            String.left 10 (isoString claim.verifiedOn)

        nameValuePairs =
            [ ( "claiming_member", Enc.string (restUrls.memberList ++ claimantIdStr ++ "/") )
            , ( "claimed_task", Enc.string (restUrls.taskList ++ taskIdStr ++ "/") )
            , ( "claimed_start_time", Enc.string startOfClaimStr )
            , ( "claimed_duration", Enc.string durationOfClaimStr )
            , ( "status", Enc.string "C" ) -- Current
            , ( "date_verified", Enc.string verifiedOnStr )
            ]

    in
        nameValuePairs |> encodeBody


makeHeaders : Credentials -> List Http.Header
makeHeaders credentials =
    case credentials of
        LoggedIn csrfToken ->
            [ Http.header "X-CSRFToken" csrfToken ]

        Token token ->
            [ Http.header "Authentication" ("Bearer " ++ token) ]


createClaim : Credentials -> RestUrls -> Claim -> (Result Http.Error String -> msg) -> Cmd msg
createClaim credentials restUrls claim result2Msg =
    let
        request = Http.request
            { method = "POST"
            , url = restUrls.claimList
            , headers = makeHeaders credentials
            , withCredentials = False
            , body = makeClaimBody claim restUrls
            , timeout = Nothing
            , expect = Http.expectString
            }
    in
        Http.send result2Msg request


updateClaim : Credentials -> RestUrls -> Int -> List (String, Enc.Value) -> (Result Http.Error String -> msg) -> Cmd msg
updateClaim credentials restUrls claimId nameValuePairs result2Msg =
    let
        request = Http.request
            { method = "PATCH"
            , url = restUrls.claimList ++ toStr (claimId) ++ "/"
            , headers = makeHeaders credentials
            , withCredentials = False
            , body = encodeBody nameValuePairs
            , timeout = Nothing
            , expect = Http.expectString
            }
    in
        Http.send result2Msg request

-----------------------------------------------------------------------------
-- CALENDAR PAGE
-----------------------------------------------------------------------------

getCalendarPage : Int -> Int -> (Result Http.Error CalendarPage -> msg) -> Cmd msg
getCalendarPage year month resultToMsg =
    let
        url = -- TODO: URL should be passed in from Django, not hard-coded here.
            "/tasks/ops-calendar-json/" ++ toStr (year) ++ "-" ++ toStr (month) ++ "/"

        request =
            Http.get url decodeCalendarPage
    in
        Http.send resultToMsg request

getCurrCalendarPage : (Result Http.Error CalendarPage -> msg) -> Cmd msg
getCurrCalendarPage resultToMsg =
    let
        url = -- TODO: URL should be passed in from Django, not hard-coded here.
            "/tasks/ops-calendar-json/"

        request =
            Http.get url decodeCalendarPage
    in
        Http.send resultToMsg request

getCurrCalendarPageForMember : String -> Int -> (Result Http.Error CalendarPage -> msg) -> Cmd msg
getCurrCalendarPageForMember csrfToken memberpk resultToMsg =
    let
      request = Http.request
        { method = "POST"
        , url = "/tasks/ops-calendar-4member-json/"  -- TODO: URL should be passed in from Django, not hard-coded here.
        , headers = [ Http.header "X-CSRFToken" csrfToken ]
        , withCredentials = False
        , body = [("memberpk", Enc.int memberpk)] |> Enc.object |> Http.jsonBody
        , timeout = Nothing
        , expect = Http.expectJson decodeCalendarPage
        }
    in
      Http.send resultToMsg request


-----------------------------------------------------------------------------
-- DECODERS
-----------------------------------------------------------------------------

decodeUser : Dec.Decoder User
decodeUser =
    decode User
        |> required "memberId" Dec.int
        |> required "name" Dec.string


decodeOpsTask : Dec.Decoder OpsTask
decodeOpsTask =
    decode OpsTask
        |> required "taskId" Dec.int
        |> required "isoDate" Dec.string
        |> required "shortDesc" Dec.string
        |> required "timeWindow" (Dec.nullable decodeTimeWindow)
        |> required "instructions" Dec.string
        |> required "staffingStatus" Dec.string
        |> required "possibleActions" (Dec.list Dec.string)
        |> required "staffedBy" (Dec.list Dec.string)
        |> required "taskStatus" Dec.string
        |> required "usersClaimId" (Dec.nullable Dec.int)


decodeDayOfTasks : Dec.Decoder DayOfTasks
decodeDayOfTasks =
    decode DayOfTasks
        |> required "dayOfMonth" Dec.int
        |> required "isInTargetMonth" Dec.bool
        |> required "isToday" Dec.bool
        |> required "tasks" (Dec.list decodeOpsTask)


decodeCalendarPage : Dec.Decoder CalendarPage
decodeCalendarPage =
    decode CalendarPage
        |> required "user" (Dec.nullable decodeUser)
        |> required "tasks" (Dec.list (Dec.list decodeDayOfTasks))
        |> required "year" Dec.int
        |> required "month" Dec.int


-----------------------------------------------------------------------------
-- UTILITIES
-----------------------------------------------------------------------------


toStr v =
    let
        str =
            toString v
    in
        if String.left 1 str == "\"" then
            String.dropRight 1 (String.dropLeft 1 str)
        else
            str
