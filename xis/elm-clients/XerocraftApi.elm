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
    request = Http.getString url
  in
    Http.send result2Msg request

