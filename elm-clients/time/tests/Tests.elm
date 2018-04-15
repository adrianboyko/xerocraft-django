module Tests exposing (..)

import Expect exposing (Expectation)
import Fuzz exposing (Fuzzer, int, list, string)
import Test exposing (..)
import Date exposing (Month(..))

import ClockTime exposing (ClockTime)
import CalendarDate exposing (CalendarDate)

calendarDateTest : Test
calendarDateTest =
  describe "The CalendarDate module"

    [ test "11th not 11st" <|
       \_ ->
         let someCD = {year=2018, month=Apr, day=11}
         in Expect.equal (CalendarDate.format "%ddd" someCD) "11th"

    , test "12th not 12nd" <|
       \_ ->
         let someCD = {year=2018, month=Apr, day=12}
         in Expect.equal (CalendarDate.format "%ddd" someCD) "12th"

    , test "13th not 13rd" <|
       \_ ->
         let someCD = {year=2018, month=Apr, day=13}
         in Expect.equal (CalendarDate.format "%ddd" someCD) "13th"
    ]

clockTimeTest : Test
clockTimeTest =
  describe "The ClockTime module"


    [ test "toString AM" <|
       \_ ->
         let someCT = ClockTime 11 45
         in Expect.equal (ClockTime.toString someCT) "11:45"


    , test "toString PM" <|
       \_ ->
         let someCT = ClockTime 12 30
         in Expect.equal (ClockTime.toString someCT) "12:30"


    , test "fromString AM" <|
       \_ ->
         let expectedCT = Ok (ClockTime 09 10)
         in Expect.equal (ClockTime.fromString "09:10 AM") expectedCT

    , test "fromString PM" <|
       \_ ->
         let expectedCT = Ok (ClockTime 12 40)
         in Expect.equal (ClockTime.fromString "12:40 PM") expectedCT

    ]

