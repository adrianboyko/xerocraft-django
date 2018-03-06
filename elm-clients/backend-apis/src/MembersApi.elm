module MembersApi exposing
  ( createSession
  , Flags
  , Session
  )

-- Standard
import Json.Decode as Dec
import Json.Encode as Enc
import Regex exposing (regex)
import Http

-- Third-Party

-- Local


-----------------------------------------------------------------------------
-- API SESSION
-----------------------------------------------------------------------------

type alias Session msg =
  { addDiscoveryMethods : AddDiscoveryMethods msg
  , createNewAcct : CreateNewAcct msg
  , setIsAdult : SetIsAdult msg
  }

createSession : Flags -> Session msg
createSession flags =
  { addDiscoveryMethods = addDiscoveryMethods flags
  , createNewAcct = createNewAcct flags
  , setIsAdult = setIsAdult flags
  }


-----------------------------------------------------------------------------
-- UTILITIES
-----------------------------------------------------------------------------

replaceAll : {oldSub : String, newSub : String} -> String -> String
replaceAll {oldSub, newSub} whole =
  Regex.replace Regex.All (regex oldSub) (\_ -> newSub) whole


-----------------------------------------------------------------------------
-- API TYPES
-----------------------------------------------------------------------------

type alias Flags =
  { addDiscoveryMethodUrl : String
  , csrfToken : String
  , discoveryMethodsUrl : String
  , setIsAdultUrl : String
  , uniqueKioskId : String
  , xcOrgActionUrl : String
  }


-----------------------------------------------------------------------------
-- API
-----------------------------------------------------------------------------

type alias CreateNewAcct msg = String -> String -> String -> String -> String -> (Result Http.Error String -> msg) -> Cmd msg
createNewAcct : Flags -> CreateNewAcct msg
createNewAcct flags fullName userName email password signature thing =
  let
    eq = \key value -> key++"="++value
    enc = Http.encodeUri
    formData = String.join "&"
      [ eq "action" "CheckInFirstTime"
      , eq "UserInfo-Name" (enc fullName)
      , eq "UserInfo-Username" (enc userName)
      , eq "UserInfo-Email" (enc email)
      , eq "UserInfo-Password" (enc password)
      , eq "passwordShow" "1"
      , eq "signature-uri" (enc signature)
      ]
    request = Http.request
      { method = "POST"
      , headers = []
      , url = flags.xcOrgActionUrl
      , body = Http.stringBody "application/x-www-form-urlencoded" formData
      , expect = Http.expectString
      , timeout = Nothing
      , withCredentials = False
      }
   in
     Http.send thing request

type alias SetIsAdult msg = String -> String -> Bool -> (Result Http.Error String -> msg) -> Cmd msg
setIsAdult : Flags -> SetIsAdult msg
setIsAdult flags username userpw newValue resultToMsg =
  let
    bodyObject =
      [ ("username", Enc.string username)
      , ("userpw", Enc.string userpw)
      , ("isadult", Enc.bool newValue)
      ]
    request = Http.request
      { method = "POST"
      , url = flags.setIsAdultUrl
      , headers = [ Http.header "X-CSRFToken" flags.csrfToken ]
      , withCredentials = False
      , body = bodyObject |> Enc.object |> Http.jsonBody
      , timeout = Nothing
      , expect = Http.expectString
      }
  in
    Http.send resultToMsg request

type alias AddDiscoveryMethods msg = String -> String -> List Int -> (Result Http.Error String -> msg) -> Cmd msg
addDiscoveryMethods : Flags -> AddDiscoveryMethods msg
addDiscoveryMethods flags username userpw methodPks resultToMsg =
  let
    bodyObject = \pk ->
      [ ("username", Enc.string username)
      , ("userpw", Enc.string userpw)
      , ("methodpk", Enc.int pk)
      ]
    request = \bo -> Http.request
      { method = "POST"
      , url = flags.addDiscoveryMethodUrl
      , headers = [ Http.header "X-CSRFToken" flags.csrfToken ]
      , withCredentials = False
      , body = bo |> Enc.object |> Http.jsonBody
      , timeout = Nothing
      , expect = Http.expectString
      }
    oneCmd = \req -> Http.send resultToMsg req
  in
    Cmd.batch (List.map (oneCmd << request << bodyObject) methodPks)

