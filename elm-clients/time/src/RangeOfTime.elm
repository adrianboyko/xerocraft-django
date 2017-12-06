module RangeOfTime exposing (..)

-- Standard

-- Third Party

-- Local
import PointInTime exposing (PointInTime)
import CalendarDate exposing (CalendarDate)
import ClockTime exposing (ClockTime)
import Time exposing (Time)


type alias RangeOfTime = (PointInTime, PointInTime)


{-| Returns a range that covers startCD, endCD, and everything between. -}
fromCalendarDates : CalendarDate -> CalendarDate -> RangeOfTime
fromCalendarDates startCD endCD =
  let
    (start, _) = fromCalendarDate startCD
    (_, end) = fromCalendarDate endCD
  in
    (start, end)


{-| Returns a range that covers someCD. -}
fromCalendarDate : CalendarDate -> RangeOfTime
fromCalendarDate someCD =
  let
    begin = PointInTime.fromCalendarDateAndClockTime someCD (ClockTime 00 00)
    end = begin + 24*Time.hour
  in
    (begin, end)


containsPoint : RangeOfTime -> PointInTime -> Bool
containsPoint (startPt, endPt) pt =
  startPt <= pt && pt < endPt
