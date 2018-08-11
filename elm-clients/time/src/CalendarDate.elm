module CalendarDate exposing
  ( CalendarDate
  ----------------
  , addDays
  , compare
  , dayOfWeek
  , dayOfWeekToInt
  , equal
  , format
  , fromDate
  , fromPointInTime
  , fromString
  , fromTime
  , intToMonth
  , lastOfMonth
  , monthName
  , monthToInt
  , nextMonth
  , prevMonth
  , superOrdinals
  , toString
  , toDate
  )


-- Standard
import Date exposing (Date)
import Time exposing (Time)
import Html exposing (Html, sup, span)
import Html.Attributes exposing (property)

-- Third Party
import Date.Extra.Format as DateXFormat
import Date.Extra.Create as DateXCreate
import Date.Extra.Core as DateXCore
import Date.Extra.Config.Config_en_us exposing (config)
import Date.Extra.I18n.I_en_us as EnUs
import Date.Extra.Duration as DateXDur
import String.Extra exposing (replace)
import Json.Encode exposing (string)

-- Local


----------------------------------------------------------

type alias CalendarDate =
  { year : Int
  , month : Date.Month
  , day : Int
  }


----------------------------------------------------------

{-| Produces a YYYY-MM-DD string. -}
toString : CalendarDate -> String
toString = format "%Y-%m-%d"

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
    ordinalize =
      r "11" "th" >> r "12" "th" >> r "13" "th"
      >> r "0" "th" >> r "1" "st" >> r "2" "nd" >> r "3" "rd"
      >> replace "dd" "th"
  in
    ordinalize s


-- Credit to https://gist.github.com/joakimk/57b4495fe5a4fd84506b
taggedStringToHtml: String -> Html msg
taggedStringToHtml t = span [string t |> property "innerHTML"] []


superOrdinals : String -> Html msg
superOrdinals s =
  let
    -- I'm not getting the results I want from <sup> so I'm doing something else instead:
    r dig suff = replace (dig++suff) (dig++"<span style='font-size:0.75em'>"++suff++"</span>")
    supize =
      r "0" "th" >> r "1" "st" >> r "2" "nd" >> r "3" "rd" >> r "4" "th" >>
      r "5" "th" >> r "6" "th" >> r "7" "th" >> r "8" "th" >> r "9" "th"
  in
    s |> supize |> taggedStringToHtml


----------------------------------------------------------

dayOfWeek : CalendarDate -> Date.Day
dayOfWeek d =
  d |> toDate |> Date.dayOfWeek


dayOfWeekToInt : Date.Day -> Int
dayOfWeekToInt dow =
  case dow of
    Date.Sun -> 0
    Date.Mon -> 1
    Date.Tue -> 2
    Date.Wed -> 3
    Date.Thu -> 4
    Date.Fri -> 5
    Date.Sat -> 6

----------------------------------------------------------

monthToInt : Date.Month -> Int
monthToInt = DateXCore.monthToInt

intToMonth : Int -> Date.Month
intToMonth = DateXCore.intToMonth

nextMonth : Date.Month -> Date.Month
nextMonth = DateXCore.nextMonth

prevMonth : Date.Month -> Date.Month
prevMonth = DateXCore.prevMonth

monthName : Date.Month -> String
monthName m = EnUs.monthName m

----------------------------------------------------------


toDate : CalendarDate -> Date
toDate cd =
  -- Hour/min/second are arbitrary.
  DateXCreate.dateFromFields cd.year cd.month cd.day 0 0 0 0


fromDate : Date -> CalendarDate
fromDate d =
  CalendarDate (Date.year d) (Date.month d) (Date.day d)


fromTime : Time -> CalendarDate
fromTime = Date.fromTime >> fromDate

fromPointInTime = fromTime

----------------------------------------------------------

lastOfMonth : CalendarDate -> CalendarDate
lastOfMonth cd =
  cd |> toDate |> DateXCore.lastOfMonthDate |> fromDate


addDays : Int -> CalendarDate -> CalendarDate
addDays offset cd =
  cd |> toDate |> DateXDur.add DateXDur.Day offset |> fromDate

