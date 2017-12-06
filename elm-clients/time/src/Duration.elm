module Duration exposing (..)

import Time


type alias Duration = Float


fromString : String -> Result String Duration
fromString = String.toFloat

hour = Time.hour
minute = Time.minute
second = Time.second
