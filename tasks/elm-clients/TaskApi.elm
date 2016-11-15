module TaskApi exposing
  ( Target(ForHuman, ForRest)
  , Claim, createClaim
  , Credentials
  , ClockTime, decodeClockTime, clockTimeToStr
  , Duration, durationFromString, durationToString
  , TimeWindow, decodeTimeWindow
  )

import Date exposing(Date)
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
  = None  -- Use this if the user already has a logged in session
  | Token String

createClaim : Credentials -> Claim -> (Http.RawError -> msg) -> (Http.Response -> msg) -> Cmd msg
createClaim credentials claim failure success =
  let
    -- TODO: These should be passed in from Django, not hard-coded here.
    claimUrl = "http://localhost:8000/tasks/api/claims/"
    memberUrl = "http://localhost:8000/members/api/members/"
    taskUrl = "http://localhost:8000/tasks/api/tasks/"

    claimantIdStr = toString claim.claimantId
    taskIdStr = toString claim.taskId
    startOfClaimStr = (toString claim.startOfClaim.hour) ++ ":" ++ (toString claim.startOfClaim.minute) ++ ":00"
    durationOfClaimStr = durationToString ForRest claim.durationOfClaim
    verifiedOnStr = ""

    newClaimBody =
      [ ("claiming_member", Enc.string (memberUrl ++ claimantIdStr ++ "/"))
      , ("claimed_task", Enc.string (taskUrl ++ taskIdStr ++ "/"))
      , ("claimed_start_time", Enc.string startOfClaimStr)
      , ("claimed_duration", Enc.string durationOfClaimStr)
      , ("status", Enc.string "C") -- Current
      , ("date_verified", Enc.string verifiedOnStr)
      ]
        |> Enc.object
        |> Enc.encode 0
        |> Http.string

    authHeader = case credentials of
      None -> []
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
          , url = claimUrl
          , body = newClaimBody
          }
      )
