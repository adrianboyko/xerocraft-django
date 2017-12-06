module DjangoRestFramework exposing (..)

-- Standard
import Json.Decode as Dec
import Json.Encode as Enc
import Http exposing (header)
import Char
import Regex exposing (Regex, regex, split, replace, HowMany(..))
import Time exposing (Time, hour, minute, second)
import Result.Extra as ResultX
import Date exposing (Date)
import List.Extra as ListX

-- Third-Party
import Json.Decode.Pipeline exposing (decode, required, optional, hardcoded)

-- Local
import ClockTime exposing (ClockTime)
import PointInTime exposing (PointInTime)
import Duration exposing (Duration)
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

{-| This is the specific authentication format required by DRF's TokenAuthentication
-}
authenticationHeader : String -> Http.Header
authenticationHeader token =
  Http.header "Authorization" ("Token " ++ token)


-----------------------------------------------------------------------------
-- CALENDAR DATES
-----------------------------------------------------------------------------

encodeCalendarDate : CalendarDate -> Enc.Value
encodeCalendarDate = Enc.string << CalendarDate.toString


decodeCalendarDate : Dec.Decoder CalendarDate
decodeCalendarDate =
  Dec.string |> Dec.andThen
    ( \str ->
      case (CalendarDate.fromString str) of
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
      case (clockTimeFromPythonRepr str) of
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
-- DURATION
-----------------------------------------------------------------------------

durationFromPythonRepr : String -> Result String Duration
durationFromPythonRepr s =
  let
    partsAsListString = split Regex.All (regex "[: ]") s
    partCount = List.length partsAsListString
    partsAsListResultFloat = List.map String.toFloat partsAsListString
    partsAsResultListFloat = ResultX.combine partsAsListResultFloat
    weights3 = [1*hour, 1*minute, 1*second]
    weights4 = 24*hour :: weights3
    weights = if partCount == 3 then weights3 else weights4
  in
    Result.map
      List.sum
      (Result.map2 (List.map2 (*)) (Ok weights) partsAsResultListFloat)


-- Python form for API (friendly = False): "[<days> ]<hours>:<minutes>:<seconds>"
-- User-friendly form (friendly = True): "3.5 hrs"
durationToPythonRepr : Duration -> String
durationToPythonRepr dhms =
    let
        day = 24.0 * hour
        days = dhms / day |> floor |> toFloat
        hms = dhms - (days * day)
        hours = hms / hour |> floor |> toFloat
        ms = hms - (hours * hour)
        minutes = ms / minute |> floor |> toFloat
        seconds = ms - (minutes * minute)
        pad = toString >> (String.padLeft 2 '0')
    in
        (toString days) ++ " " ++ (pad hours) ++ ":" ++ (pad minutes) ++ ":" ++ (pad seconds)


decodeDuration : Dec.Decoder Duration
decodeDuration =
  Dec.string |> Dec.andThen
    ( \str ->
      case (durationFromPythonRepr str) of
        Ok dur -> Dec.succeed dur
        Err err -> Dec.fail ("Incorrectly formatted duration: " ++ str)
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
-- URLS
-----------------------------------------------------------------------------

type alias ResourceUrl = String
type alias ResourceListUrl = String


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
  listUrl ++ (toString resNum) ++ "/"


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


httpGetRequest : String -> ResourceUrl -> Dec.Decoder a -> Http.Request a
httpGetRequest token url decoder =
  Http.request
    { method = "GET"
    , url = url
    , headers = [ authenticationHeader token ]
    , withCredentials = False
    , body = Http.emptyBody
    , timeout = Nothing
    , expect = Http.expectJson decoder
    }
