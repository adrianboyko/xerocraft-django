module Tests exposing (..)

import Expect exposing (Expectation, fail)
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
    , test "Parse 2018-09-21" <|
       \_ ->
         let someCD = CalendarDate.fromString "2018-09-21"
         in case someCD of
           Ok cd -> Expect.equal cd (CalendarDate.CalendarDate 2018 Sep 21)
           Err s -> fail s
    , test "Parse XXXX-09-21" <|
       \_ ->
         let someCD = CalendarDate.fromString "XXXX-09-21"
         in Expect.err someCD
    , test "Parse 2018-09-21-99" <|
       \_ ->
         let someCD = CalendarDate.fromString "2018-09-21-99"
         in Expect.err someCD
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

    , test "toString Top of Hour" <|
       \_ ->
         let someCT = ClockTime 12 00
         in Expect.equal (ClockTime.toString someCT) "12:00"

    , test "toString single digit hour and minute" <|
       \_ ->
         let someCT = ClockTime 9 5
         in Expect.equal (ClockTime.toString someCT) "09:05"

    , test "fromString AM" <|
       \_ ->
         let expectedCT = Ok (ClockTime 09 10)
         in Expect.equal (ClockTime.fromString "09:10 AM") expectedCT

    , test "fromString PM" <|
       \_ ->
         let expectedCT = Ok (ClockTime 12 40)
         in Expect.equal (ClockTime.fromString "12:40 PM") expectedCT

    ]

