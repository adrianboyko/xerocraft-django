module DjangoRestApiTests exposing (..)

import Time

import Expect exposing (Expectation)
import Fuzz exposing (Fuzzer, int, list, string, floatRange)
import Test exposing (..)

import DjangoRestFramework as DRF

suite : Test
suite =
  describe "Django Rest API Tests"

    [ fuzz (floatRange (1*Time.minute) (24*Time.hour)) "Any float is a duration" <|
        \aFloat ->
          aFloat
          |> DRF.durationToPythonRepr  -- |> Debug.log (toString aFloat)
          |> String.length
          |> Expect.equal 10  -- I.e. Length of "D HH:MM:SS" is 10
    ]
