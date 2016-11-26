module TaskApi exposing
  ( Target(ForHuman, ForRest)
  , Claim, createClaim
  , Credentials(LoggedIn, Token)
  , ClockTime, decodeClockTime, clockTimeToStr
  , Duration, durationFromString, durationToString
  , TimeWindow, decodeTimeWindow
  , RestUrls
  )

import Date exposing(Date)
import Date.Extra.Format exposing (isoString)
import Time exposing (Time, hour, minute, second)
import Json.Encode as Enc
import Json.Decode as Dec exposing((:=), maybe)

-- elm-package install --yes elm-community/elm-json-extra
import Json.Decode.Extra exposing ((|:))

import Task exposing (Task)
import Regex exposing (Regex, regex, split)
import List
import Http
import String

type Target = ForHuman | ForRest

-----------------------------------------------------------------------------
-- TIME WINDOW
-----------------------------------------------------------------------------

type alias RestUrls =
  { memberList: String
  , taskList: String
  , claimList: String
  }

-----------------------------------------------------------------------------
-- TIME WINDOW
-----------------------------------------------------------------------------

type alias TimeWindow =
  { begin: ClockTime
  , duration: Duration
  }

decodeTimeWindow : Dec.Decoder TimeWindow
decodeTimeWindow =
  Dec.succeed TimeWindow
    |: ("begin"    := decodeClockTime)
    |: ("duration" := Dec.float)

-----------------------------------------------------------------------------
-- CLOCK TIME
-----------------------------------------------------------------------------

type alias ClockTime =
  { hour: Int    -- Value must be 0 to 23, inclusive
  , minute: Int  -- Value must be 0 to 59, inclusive
  }

decodeClockTime : Dec.Decoder ClockTime
decodeClockTime =
  Dec.succeed ClockTime
    |: ("hour"   := Dec.int)
    |: ("minute" := Dec.int)

clockTimeToStr : ClockTime -> String
clockTimeToStr ct =
  let
    hour = String.padLeft 2 '0' (toString ct.hour)
    minute = String.padLeft 2 '0' (toString ct.minute)
  in
    hour ++ ":" ++ minute

-----------------------------------------------------------------------------
-- DURATION
-----------------------------------------------------------------------------

type alias Duration = Float  -- A time duration in milliseconds, so we can use core Time's units.

durationFromString: String -> Duration
durationFromString s =
  let
    unResult = \x -> case x of
      Ok val -> val
      Err str -> Debug.crash str
    partsAsStrs = split Regex.All (regex "[: ]") s
    partsAsResults = List.map String.toFloat partsAsStrs
    partsAsFloats = List.map unResult partsAsResults
    weights3 = [hour, minute, second]
    weights4 = [24*hour] ++ weights3
    weights = if (List.length partsAsFloats) == 4 then weights4 else weights3
  in
    List.foldr (+) 0 (List.map2 (*) weights partsAsFloats)

-- Python form for API (friendly = False): "[<days> ]<hours>:<minutes>:<seconds>"
-- User-friendly form (friendly = True): "3.5 hrs"
durationToString: Target -> Duration -> String
durationToString target dhms =
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
    case target of
      ForHuman ->
        -- TODO: This is only good for tasks that are less than a day long, which suffices for now.
        toString (hours + minutes/60.0) ++ " hrs"
      ForRest ->
        (toString days) ++ " " ++ (pad hours) ++ ":" ++ (pad minutes) ++ ":" ++ (pad seconds)


-----------------------------------------------------------------------------
-- CLAIM
-----------------------------------------------------------------------------

type alias Claim =
  { taskId: Int
  , claimantId: Int  -- Must be a member id, not a user id.
  , startOfClaim: ClockTime
  , durationOfClaim: Duration
  , verifiedOn: Date
  }

type Credentials
  = LoggedIn String -- Use this if the user already has a logged in session. String is the csrfToken.
  | Token String

makeClaimBody : Claim -> RestUrls -> Http.Body
makeClaimBody claim restUrls =
  let

    claimantIdStr = toString claim.claimantId
    taskIdStr = toString claim.taskId
    startOfClaimStr = (toString claim.startOfClaim.hour) ++ ":" ++ (toString claim.startOfClaim.minute) ++ ":00"
    durationOfClaimStr = durationToString ForRest claim.durationOfClaim
    verifiedOnStr = String.left 10 (isoString claim.verifiedOn)

    in
      [ ("claiming_member", Enc.string (restUrls.memberList ++ claimantIdStr ++ "/"))
      , ("claimed_task", Enc.string (restUrls.taskList ++ taskIdStr ++ "/"))
      , ("claimed_start_time", Enc.string startOfClaimStr)
      , ("claimed_duration", Enc.string durationOfClaimStr)
      , ("status", Enc.string "C") -- Current
      , ("date_verified", Enc.string verifiedOnStr)
      ]
        |> Enc.object
        |> Enc.encode 0
        |> Http.string


createClaim : Credentials -> RestUrls -> Claim -> (Http.RawError -> msg) -> (Http.Response -> msg) -> Cmd msg
createClaim credentials restUrls claim failure success =
  let
    authHeader = case credentials of
      LoggedIn csrfToken -> [("X-CSRFToken", csrfToken)]
      Token token -> [("Authentication", "Bearer " ++ token)]
  in
    Task.perform
      failure
      success
      (
        Http.send
          Http.defaultSettings
          { verb = "POST"
          , headers = [("Content-Type", "application/json")] ++ authHeader
          , url = restUrls.claimList
          , body = makeClaimBody claim restUrls
          }
      )
