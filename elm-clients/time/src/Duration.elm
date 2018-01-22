module Duration exposing
  ( Duration
  , fromString
  , ticksPerHour
  , ticksPerMinute
  , ticksPerSecond
  , toString
  )

import Time
import Basics


type alias Duration = Float


fromString : String -> Result String Duration
fromString = String.toFloat


toString : Duration -> String
toString dur =
  -- TODO: This is only good for tasks that are less than a day long, which suffices for now.
  let
    hrs = dur |> Time.inHours |> floor
    mins = dur - (toFloat hrs) * ticksPerHour |> Time.inMinutes |> floor
  in
    if hrs + mins == 0 then
      "0"
    else
      let
        hrsStr = toPluralStr hrs "hr"
        minsStr = toPluralStr mins "min"
      in
        String.join " " [hrsStr, minsStr] |> String.trim


toPluralStr : Int -> String -> String
toPluralStr n unit =
  let
    ending = if n/=1 then "s" else ""
  in
    if n == 0 then ""
    else (Basics.toString n) ++ " " ++ unit ++ ending


ticksPerHour = Time.hour
ticksPerMinute = Time.minute
ticksPerSecond = Time.second
