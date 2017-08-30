module XerocraftApi exposing (..)

-- Standard
import Http

-- Third-Party

-- Local

-----------------------------------------------------------------------------
--
-----------------------------------------------------------------------------

scrapeXcOrgLogins : String -> (Result Http.Error String -> msg) -> Cmd msg
scrapeXcOrgLogins url result2Msg =
  let
    testUrl = url ++ "kfritz//"
    request = Http.getString testUrl  -- TODO: This shouldn't be testUrl for production.
  in
    Http.send result2Msg request

