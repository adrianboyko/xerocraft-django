module DjangoRestFramework exposing (..)

-- Standard
import Json.Decode as Dec
import Http exposing (header)
import Char

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


-- Example "https://localhost:8000/ops/api/time_block_types/4/" -> 4
getIdFromUrl : String -> Result String Int
getIdFromUrl url =
  let
    parts = String.split "/" url
    numberStrs = parts |> List.filter (not << String.isEmpty) |> List.filter (String.all Char.isDigit)
    numberStr = Maybe.withDefault "FOO" (List.head numberStrs)
  in
    if List.length numberStrs /= 1
      then
        Err "Unhandled URL format."
      else
        String.toInt numberStr



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

