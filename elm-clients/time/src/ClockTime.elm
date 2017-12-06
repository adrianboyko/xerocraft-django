module ClockTime exposing (..)

-- Standard
import Time exposing (Time)
import Date exposing (Date)

-- Third party
import Date.Extra.Create as DateXCreate
import Date.Extra.Format as DateXFormat
import Date.Extra.Config.Config_en_us exposing (config)
import String.Extra as StringX
import List.Extra as ListX

-- Local

----------------------------------------------------------

type alias ClockTime =
  { hour : Int  -- Value must be 0 to 23, inclusive
  , minute : Int  -- Value must be 0 to 59, inclusive
  }


----------------------------------------------------------

toString : ClockTime -> String
toString ct =
  let
    stringParts = List.map Basics.toString [ct.hour, ct.minute]
  in
    String.join ":" stringParts

{-| Assumes that given string is from a human and requires that AM or PM be explicitly included
because a value like 9:45 is ambiguous when coming from a human. -}
fromString : String -> Result String ClockTime
fromString s =
  let
    s2 = s |> String.trim |> String.toLower
    isPM = String.endsWith "pm" s2
    isAM = String.endsWith "am" s2
    s3 = s2 |> StringX.replace "pm" "" |> StringX.replace "am" "" |> String.trim
    hrMinList = String.split ":" s3
    hrMemb = List.head hrMinList
    minMemb = ListX.last hrMinList
    hr = Maybe.map String.toInt hrMemb
    min = Maybe.map String.toInt minMemb
  in
    case (xor isAM isPM, hr, min) of

      (False, _, _) ->
        Err "Please specify AM or PM."

      (True, Just (Ok hr), Just (Ok min)) ->
        (Ok <| ClockTime (hr + if isPM && hr<12 then 12 else 0) min)

      _ ->
        Err "Please specify HH:MM AM/PM."


format : String -> ClockTime -> String
format fmt ct =
  let
    d = DateXCreate.dateFromFields 0 Date.Jan 0 ct.hour ct.minute 0 0
  in
    DateXFormat.format config fmt d


fromTime : Time -> ClockTime
fromTime t =
  let
    d = Date.fromTime t
  in
    ClockTime (Date.hour d) (Date.minute d)