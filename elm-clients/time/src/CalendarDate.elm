module CalendarDate exposing
  ( CalendarDate
  , DayOfWeek(..)
  ----------------
  , addDays
  , compare
  , dayOfWeek
  , dayOfWeekToInt
  , equal
  , format
  , fromDate
  , fromString
  , lastOfMonth
  , toString
  , toDate
  )


-- Standard
import Date exposing (Date)
import Time exposing (Time)

-- Third Party
import Date.Extra.Format as DateXFormat
import Date.Extra.Create as DateXCreate
import Date.Extra.Core as DateXCore
import Date.Extra.Config.Config_en_us exposing (config)
import Date.Extra.Duration as DateXDur
import String.Extra as StringX exposing (replace)

-- Local


----------------------------------------------------------

type alias CalendarDate =
  { year : Int
  , month : Date.Month
  , day : Int
  }

type DayOfWeek
  = Sun
  | Mon
  | Tue
  | Wed
  | Thu
  | Fri
  | Sat

----------------------------------------------------------

{-| Produces a YYYY-MM-DD string. -}
toString : CalendarDate -> String
toString =
  (DateXFormat.format config "%Y-%m-%d") << toDate


{-| Parses strings that are bare dates without a time part. -}
fromString : String -> Result String CalendarDate
fromString s =
  let
    -- Note: Javascript (and hence Elm) treats a bare date string as being UTC.
    -- If "00:00:00" is added to the date, it treats string as being in local timezone.
    s2 = s ++ " 00:00:00"
  in
    Result.map
      (\x -> CalendarDate (Date.year x) (Date.month x) (Date.day x))
      (Date.fromString (s ++ " 00:00:00"))


----------------------------------------------------------

compare : CalendarDate -> CalendarDate -> Order
compare x y =
  Basics.compare (toString x) (toString y)


equal : CalendarDate -> CalendarDate -> Bool
equal x y =
    x.year == y.year && x.month == y.month && x.day == y.day


----------------------------------------------------------

format : String -> CalendarDate -> String
format fmt cd =
  let
    fmtMod = replace "%ddd" "%edd" fmt
    d = toDate cd
    s = DateXFormat.format config fmtMod d
    r dig suff = replace (dig++"dd") (dig++suff)
    -- ordinalize supports the non-standard %ddd formatting option.
    ordinalize = r "0" "th" >> r "1" "st" >> r "2" "nd" >> r "3" "rd" >> replace "dd" "th"
  in
    ordinalize s

----------------------------------------------------------

dayOfWeek : CalendarDate -> DayOfWeek
dayOfWeek d =
  case d |> toDate |> Date.dayOfWeek of
    Date.Sun -> Sun
    Date.Mon -> Mon
    Date.Tue -> Tue
    Date.Wed -> Wed
    Date.Thu -> Thu
    Date.Fri -> Fri
    Date.Sat -> Sat


dayOfWeekToInt : DayOfWeek -> Int
dayOfWeekToInt dow =
  case dow of
    Sun -> 0
    Mon -> 1
    Tue -> 2
    Wed -> 3
    Thu -> 4
    Fri -> 5
    Sat -> 6


----------------------------------------------------------


toDate : CalendarDate -> Date
toDate cd =
  -- Hour/min/second are arbitrary.
  DateXCreate.dateFromFields cd.year cd.month cd.day 0 0 0 0


fromDate : Date -> CalendarDate
fromDate d =
  CalendarDate (Date.year d) (Date.month d) (Date.day d)


----------------------------------------------------------

lastOfMonth : CalendarDate -> CalendarDate
lastOfMonth cd =
  cd |> toDate |> DateXCore.lastOfMonthDate |> fromDate


addDays : Int -> CalendarDate -> CalendarDate
addDays offset cd =
  cd |> toDate |> DateXDur.add DateXDur.Day offset |> fromDate

