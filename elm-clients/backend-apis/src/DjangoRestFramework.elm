module DjangoRestFramework exposing (..)

-- Standard
import Json.Decode as Dec
import Json.Encode as Enc
import Http
import Char
import Regex exposing (regex, split, replace, HowMany(..))
import Time exposing (Time)
import Result.Extra as ResultX
import Date exposing (Date)
import List.Extra as ListX

-- Third-Party
import Json.Decode.Pipeline exposing (decode, required)

-- Local
import ClockTime exposing (ClockTime)
import PointInTime exposing (PointInTime)
import Duration exposing (Duration, ticksPerSecond, ticksPerMinute, ticksPerHour)
import CalendarDate exposing (CalendarDate)


-----------------------------------------------------------------------------
-- TYPES
-----------------------------------------------------------------------------

-- Following is the response format of Django Rest Framework
type alias PageOf a =
  { count : Int
  , next : Maybe String
  , previous: Maybe String
  , results: List a
  }


-----------------------------------------------------------------------------
-- UTILITIES
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- CALENDAR DATES
-----------------------------------------------------------------------------

encodeCalendarDate : CalendarDate -> Enc.Value
encodeCalendarDate = Enc.string << CalendarDate.toString


decodeCalendarDate : Dec.Decoder CalendarDate
decodeCalendarDate =
  Dec.string |> Dec.andThen
    ( \str ->
      case CalendarDate.fromString str of
        Ok cd -> Dec.succeed cd
        Err err -> Dec.fail err
    )

-----------------------------------------------------------------------------
-- CLOCK TIME
-----------------------------------------------------------------------------


clockTimeToString : Maybe ClockTime -> String
clockTimeToString clockTime =
  case clockTime of
    Just ct -> clockTimeToPythonRepr ct
    Nothing -> "--:--"


clockTimeToPythonRepr : ClockTime -> String
clockTimeToPythonRepr ct =
    let
        hour = String.padLeft 2 '0' (toString ct.hour)
        minute = String.padLeft 2 '0' (toString ct.minute)
    in
        hour ++ ":" ++ minute


clockTimeFromPythonRepr : String -> Result String ClockTime
clockTimeFromPythonRepr s =
    let
        parts = split Regex.All (regex "[:]") s
        hourResult = parts |> ListX.getAt 0 |> Maybe.map String.toInt
        minuteResult = parts |> ListX.getAt 1 |> Maybe.map String.toInt
    in
        case (hourResult, minuteResult) of
           (Just (Ok hour), Just (Ok minute)) -> Ok (ClockTime hour minute)
           _ -> Err (s ++ " is an invalid clock time")


decodeClockTime : Dec.Decoder ClockTime
decodeClockTime =
  Dec.string |> Dec.andThen
    ( \str ->
      case clockTimeFromPythonRepr str of
        Ok ct -> Dec.succeed ct
        Err err -> Dec.fail err
    )


encodeClockTime : ClockTime -> Enc.Value
encodeClockTime = Enc.string << clockTimeToPythonRepr


clockTimeFromDate : Date -> ClockTime
clockTimeFromDate d = ClockTime (Date.hour d) (Date.minute d)


clockTimeFromTime : Time -> ClockTime
clockTimeFromTime t = t |> Date.fromTime |> clockTimeFromDate


-----------------------------------------------------------------------------
-- POINT-IN-TIME
-----------------------------------------------------------------------------

decodePointInTime : Dec.Decoder PointInTime
decodePointInTime =
  Dec.string |> Dec.andThen
    ( \str ->
      case PointInTime.fromString str of
        Ok pit -> Dec.succeed pit
        Err err -> Dec.fail err
    )

encodePointInTime : PointInTime -> Enc.Value
encodePointInTime =
  PointInTime.isoString >> Enc.string


-----------------------------------------------------------------------------
-- DURATION
-----------------------------------------------------------------------------

durationFromPythonRepr : String -> Result String Duration
durationFromPythonRepr s =
  let
    partsAsListString = split Regex.All (regex "[: ]") s
    partCount = List.length partsAsListString
    partsAsListResultFloat = List.map String.toFloat partsAsListString
    partsAsResultListFloat = ResultX.combine partsAsListResultFloat
    weights3 = [1*ticksPerHour, 1*ticksPerMinute, 1*ticksPerSecond]
    weights4 = 24*ticksPerHour :: weights3
    weights = if partCount == 3 then weights3 else weights4
  in
    Result.map
      List.sum
      (Result.map2 (List.map2 (*)) (Ok weights) partsAsResultListFloat)


-- Python form for API (friendly = False): "[<days> ]<hours>:<minutes>:<seconds>"
-- User-friendly form (friendly = True): "3.5 hrs"
durationToPythonRepr : Duration -> String
durationToPythonRepr dur1 =
    let
        day = 24.0 * ticksPerHour

        daysInt = dur1 / day |> floor
        dur2 = dur1 - toFloat daysInt * day

        hoursInt = dur2 / ticksPerHour |> floor
        dur3 = dur2 - toFloat hoursInt * ticksPerHour

        minsInt = dur3 / ticksPerMinute |> floor
        dur4 = dur3 - toFloat minsInt * ticksPerMinute

        secsInt = dur4 / ticksPerSecond |> floor

        pad = toString >> String.padLeft 2 '0'
    in
        toString daysInt ++ " " ++ pad hoursInt ++ ":" ++ pad minsInt ++ ":" ++ pad secsInt


decodeDuration : Dec.Decoder Duration
decodeDuration =
  Dec.string |> Dec.andThen
    -- Could use Json.Decode.Extra.fromResult here, but that wouldn't allow friendlier error msg.
    ( \str ->
      case durationFromPythonRepr str of
        Ok dur -> Dec.succeed dur
        Err _ -> Dec.fail ("Incorrectly formatted duration: " ++ str)
    )


encodeDuration : Duration -> Enc.Value
encodeDuration = Enc.string << durationToPythonRepr


-----------------------------------------------------------------------------
-- PAGES
-----------------------------------------------------------------------------

decodePageOf : Dec.Decoder a -> Dec.Decoder (PageOf a)
decodePageOf decoder =
  decode PageOf
    |> required "count" Dec.int
    |> required "next" (Dec.maybe Dec.string)
    |> required "previous" (Dec.maybe Dec.string)
    |> required "results" (Dec.list decoder)


-----------------------------------------------------------------------------
-- RESOURCES
-----------------------------------------------------------------------------

-- On the Elm side, resources have an id/data structure.

type alias Resource a = { id : Int, data : a }

-- On the Django side, resources have flat id+data structure.

decodeResource : Dec.Decoder a -> Dec.Decoder (Resource a)
decodeResource dataDecoder =
  Dec.map2 Resource
    (Dec.field "id" Dec.int)
    dataDecoder

encodeResource : (a -> List (String, Enc.Value)) -> Resource a -> Enc.Value
encodeResource dataNVPer res =
  Enc.object (("id", Enc.int res.id) :: dataNVPer res.data)


-----------------------------------------------------------------------------
-- URLS
-----------------------------------------------------------------------------

type alias ServiceUrl = String
type alias ResourceUrl = String
type alias ResourceListUrl = String
type alias PageUrl = String

extractRelativeUrl : ResourceUrl -> ResourceUrl
extractRelativeUrl url =
  let
    urlBaseRegex = regex "^.+?[^\\/:](?=[?\\/]|$)"
  in
    replace (AtMost 1) urlBaseRegex (always "") url


-- This decoder strips the URL base off of the resource url.
decodeResourceUrl : Dec.Decoder ResourceUrl
decodeResourceUrl =
  Dec.string |> Dec.andThen
    ( \str -> Dec.succeed (extractRelativeUrl str))


urlFromId : ResourceListUrl -> Int -> ResourceUrl
urlFromId listUrl resNum =
  listUrl ++ toString resNum ++ "/"


-- Example "https://localhost:8000/ops/api/time_block_types/4/" -> 4
idFromUrl : String -> Result String Int
idFromUrl url =
  let
    parts = String.split "/" url
    numberStrs = parts |> List.filter (not << String.isEmpty) |> List.filter (String.all Char.isDigit)
    numberStr = Maybe.withDefault "FOO" (List.head numberStrs)
  in
    if List.length numberStrs /= 1
      then
        Err "Unhandled URL format."
      else
        String.toInt numberStr


-----------------------------------------------------------------------------
--
-----------------------------------------------------------------------------

type Authorization
  = NoAuthorization
  | LoggedIn String -- Logged in with CSRF token
  | Token String  -- A token registered with Django.


authenticationHeader : Authorization -> Http.Header
authenticationHeader auth =
  case auth of
    Token t -> Http.header "Authorization" ("Token " ++ t) -- Django auth token
    LoggedIn t -> Http.header "X-CSRFToken" t
    NoAuthorization -> Http.header "X-NoAuth" "NoAuth"


getRequest : Authorization -> ResourceUrl -> Dec.Decoder a -> Http.Request a
getRequest auth url decoder =
  Http.request
    { method = "GET"
    , url = url
    , headers = [ authenticationHeader auth ]
    , withCredentials = False
    , body = Http.emptyBody
    , timeout = Nothing
    , expect = Http.expectJson decoder
    }

deleteRequest : Authorization -> ResourceUrl -> Http.Request String
deleteRequest auth url =
  Http.request
    { method = "DELETE"
    , url = url
    , headers = [ authenticationHeader auth ]
    , withCredentials = False
    , body = Http.emptyBody
    , timeout = Nothing
    , expect = Http.expectString
    }

postRequest : Authorization -> String -> Dec.Decoder a -> Enc.Value -> Http.Request a
postRequest auth url responseDecoder encodedData =
  Http.request
    { method = "POST"
    , headers = [authenticationHeader auth]
    , url = url
    , body = encodedData |> Http.jsonBody
    , expect = Http.expectJson responseDecoder
    , timeout = Nothing
    , withCredentials = False
    }

postRequestExpectingString : Authorization -> String -> Enc.Value -> Http.Request String
postRequestExpectingString auth url encodedData =
  Http.request
    { method = "POST"
    , headers = [authenticationHeader auth]
    , url = url
    , body = encodedData |> Http.jsonBody
    , expect = Http.expectString
    , timeout = Nothing
    , withCredentials = False
    }
