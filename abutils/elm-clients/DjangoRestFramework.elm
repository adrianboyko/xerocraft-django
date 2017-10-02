module DjangoRestFramework exposing (..)

-- Standard
import Json.Decode as Dec
import Http exposing (header)

-- Third-Party
import Json.Decode.Pipeline exposing (decode, required, optional, hardcoded)

-- Local


-----------------------------------------------------------------------------
-- TYPES
-----------------------------------------------------------------------------

-- Following is the response format of Django Rest Framework
type alias PageOf a =
  { count : Int
  , next : Maybe String
  , previous: Maybe String
  , results: List a
  }

-----------------------------------------------------------------------------
-- UTILITIES
-----------------------------------------------------------------------------

{-| This is the specific authentication format required by DRF's TokenAuthentication
-}
authenticationHeader : String -> Http.Header
authenticationHeader token =
  Http.header "Authorization" ("Token " ++ token)


-----------------------------------------------------------------------------
-- JSON
-----------------------------------------------------------------------------

decodePageOf : Dec.Decoder a -> Dec.Decoder (PageOf a)
decodePageOf decoder =
  decode PageOf
    |> required "count" Dec.int
    |> required "next" (Dec.maybe Dec.string)
    |> required "previous" (Dec.maybe Dec.string)
    |> required "results" (Dec.list decoder)

