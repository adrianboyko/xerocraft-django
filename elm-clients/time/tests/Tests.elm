module Tests exposing (..)

import Expect exposing (Expectation)
import Fuzz exposing (Fuzzer, int, list, string)
import Test exposing (..)


import ClockTime exposing (ClockTime)

suite : Test
suite =
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

