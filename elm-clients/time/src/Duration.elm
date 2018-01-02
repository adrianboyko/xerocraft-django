module Duration exposing (..)

import Time
import Basics

type alias Duration = Float


fromString : String -> Result String Duration
fromString = String.toFloat

toString : Duration -> String
toString dhms =
  let
    day = 24.0 * hour
    days = dhms / day |> floor |> toFloat
    hms = dhms - (days * day)
    hours = hms / hour |> floor |> toFloat
    ms = hms - (hours * hour)
    minutes = ms / minute |> floor |> toFloat
    seconds = ms - (minutes * minute)
    pad = Basics.toString >> (String.padLeft 2 '0')
  in
    -- TODO: This is only good for tasks that are less than a day long, which suffices for now.
    Basics.toString (hours + minutes / 60.0) ++ " hrs"

hour = Time.hour
minute = Time.minute
second = Time.second
