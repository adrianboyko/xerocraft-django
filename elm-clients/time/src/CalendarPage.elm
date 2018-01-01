module CalendarPage exposing (..)

-- Standard
import Date exposing (Month, Day)

-- Third Party
import List.Split exposing (chunksOfLeft)
import List.Extra as ListX

-- Local
import CalendarDate as CD exposing (CalendarDate)

-----------------------------------------------------

type alias CalendarSquare a =
  { calendarDate : CalendarDate
  , data : Maybe a
  }

type alias CalendarRow a =
  List (CalendarSquare a)

type alias CalendarPage a =
  { year : Int
  , month : Month
  , rows : List (CalendarRow a)
  }

-----------------------------------------------------

calendarPage : Int -> Month -> CalendarPage a
calendarPage year month =
  let
    -- Figure out the cal date that the page starts with. It's usually not in year/month.
    firstOfMonth = CalendarDate year month 1
    offsetToStart = 0 - (firstOfMonth |> CD.dayOfWeek |> CD.dayOfWeekToInt)
    pageStart = CD.addDays offsetToStart firstOfMonth

    -- Figure out the cal date that the page ends with. It's usually not in year/month.
    lastOfMonth = CD.lastOfMonth firstOfMonth
    offsetToEnd = 6 - (lastOfMonth |> CD.dayOfWeek |> CD.dayOfWeekToInt)
    pageEnd = CD.addDays offsetToEnd lastOfMonth

    squareCount = lastOfMonth.day + (abs offsetToStart) + offsetToEnd  -- ASSERT: Is a multiple of 7.
    squareNums = List.range 0 (squareCount - 1)
    squares = List.map (\num -> CalendarSquare (CD.addDays num pageStart) Nothing) squareNums

  in
    CalendarPage year month (chunksOfLeft 7 squares)  -- ASSERT: EVERY member must have length 7.


mapToList : (CalendarSquare a -> b) -> CalendarPage a -> List b
mapToList f calendar =
  let
    squares = List.concat calendar.rows
  in
    List.map f squares


update : CalendarDate -> Maybe a -> CalendarPage a -> CalendarPage a
update targetCalDate data oldCal =
  let
    oldSquares = List.concat oldCal.rows
    isSquareToUpdate sq = CD.equal sq.calendarDate targetCalDate
    newSquare = CalendarSquare targetCalDate data
    updatedSquares = ListX.replaceIf isSquareToUpdate newSquare oldSquares
  in
    CalendarPage oldCal.year oldCal.month (chunksOfLeft 7 updatedSquares)

