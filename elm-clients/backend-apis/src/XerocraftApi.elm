module XerocraftApi exposing (..)

-- Standard
import Http
import Json.Encode as Enc

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


cloneAcctToXis : String -> String -> String -> String -> (Result Http.Error String -> msg) -> Cmd msg
cloneAcctToXis url csrfToken username userpw resultToMsg =
  let
    bodyObj =
      [ ("username", Enc.string username)
      , ("userpw", Enc.string userpw)
      ]
    request = Http.request
      { method = "POST"
      , url = url
      , headers = [ Http.header "X-CSRFToken" csrfToken ]
      , withCredentials = False
      , body = bodyObj |> Enc.object |> Http.jsonBody
      , timeout = Nothing
      , expect = Http.expectString
      }
  in
    Http.send resultToMsg request

