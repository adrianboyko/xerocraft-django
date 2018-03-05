module PointInTime exposing (..)

-- Standard
import Task exposing (Task)
import Time exposing (..)
import Date exposing (..)

-- Third Party
import Date.Extra.Create as DateXCreate
import Date.Extra.Format as DateXFmt

-- Local
import ClockTime exposing (ClockTime)
import CalendarDate exposing (CalendarDate)

----------------------------------------------------------

type alias PointInTime = Time  -- Which is a Float


----------------------------------------------------------

now : Task x PointInTime
now = Time.now

fromString : String -> Result String PointInTime
fromString s =
  let
    date = Date.fromString s
  in
    case date of
      Ok d -> Ok (Date.toTime d)
      Err e -> Err e


fromCalendarDateAndClockTime: CalendarDate -> ClockTime -> PointInTime
fromCalendarDateAndClockTime cd ct =
  let
    d = DateXCreate.dateFromFields cd.year cd.month cd.day ct.hour ct.minute 0 0
  in
    Date.toTime d


toClockTime : PointInTime -> ClockTime
toClockTime pt = ClockTime (hour pt) (minute pt)


toCalendarDate: PointInTime -> CalendarDate
toCalendarDate pt = CalendarDate (year pt) (month pt) (dayOfMonth pt)


isoString: PointInTime -> String
isoString = Date.fromTime >> DateXFmt.isoString

----------------------------------------------------------

year : PointInTime -> Int
year = Date.fromTime >> Date.year

month : PointInTime -> Month
month = Date.fromTime >> Date.month

dayOfMonth : PointInTime -> Int
dayOfMonth = Date.fromTime >> Date.day

dayOfWeek : PointInTime -> Day
dayOfWeek = Date.fromTime >> Date.dayOfWeek

hour : PointInTime -> Int
hour = Date.fromTime >> Date.hour

minute : PointInTime -> Int
minute = Date.fromTime >> Date.minute

second : PointInTime -> Int
second = Date.fromTime >> Date.second

millisecond : PointInTime -> Int
millisecond = Date.fromTime >> Date.millisecond

