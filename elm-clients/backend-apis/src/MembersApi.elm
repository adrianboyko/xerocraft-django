module MembersApi exposing
  ( createSession
  , Flags
  , MatchingAcct
  , MatchingAcctInfo
  , GenericResult
  , VisitEventType (..)
  , ReasonForVisit (..)
  , Session
  )

-- Standard
import Date as Date
import Json.Decode as Dec
import Json.Encode as Enc
import Json.Decode.Extra as DecX
import Regex exposing (regex)
import Http
import Time exposing (Time)

-- Third-Party
import Json.Decode.Pipeline exposing (decode, required, hardcoded)

-- Local
import DjangoRestFramework as DRF exposing (PageOf, decodePageOf, authenticationHeader)


-----------------------------------------------------------------------------
-- API SESSION
-----------------------------------------------------------------------------

type alias Session msg =
  { addDiscoveryMethods : AddDiscoveryMethods msg
  , createNewAcct : CreateNewAcct msg
  , getMatchingAccts : GetMatchingAccts msg
  , getCheckedInAccts : GetCheckedInAccts msg
  , logArrivalEvent : LogArrivalEvent msg
  , logDepartureEvent : LogDepartureEvent msg
  , setIsAdult : SetIsAdult msg
  }

createSession : Flags -> Session msg
createSession flags =
  { addDiscoveryMethods = addDiscoveryMethods flags
  , createNewAcct = createNewAcct flags
  , getMatchingAccts = getMatchingAccts flags
  , getCheckedInAccts = getCheckedInAccts flags
  , logArrivalEvent = logArrivalEvent flags
  , logDepartureEvent = logDepartureEvent flags
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
  , checkedInAcctsUrl : String
  , csrfToken : String
  , discoveryMethodsUrl : String
  , logVisitEventUrl : String
  , matchingAcctsUrl : String
  , setIsAdultUrl : String
  , uniqueKioskId : String
  , xcOrgActionUrl : String
  }

type alias MatchingAcct =
  { userName : String
  , memberNum : Int
  }

type alias MatchingAcctInfo =
  { target : String
  , matches : List MatchingAcct
  }

type alias GenericResult =
  { result : String
  }

type VisitEventType
  = Arrival
  | Present
  | Departure

type ReasonForVisit
  = Curiousity
  | ClassParticipant
  | MemberPrivileges
  | ClubPrivileges
  | GuestOfMember
  | Volunteer
  | Other

-----------------------------------------------------------------------------
-- API
-----------------------------------------------------------------------------

type alias GetCheckedInAccts msg = (Result Http.Error MatchingAcctInfo -> msg) -> Cmd msg
getCheckedInAccts: Flags -> GetCheckedInAccts msg
getCheckedInAccts flags resultToMsg =
  let
    url = flags.checkedInAcctsUrl++"?format=json"  -- Easier than an "Accept" header.
    request = Http.get url decodeMatchingAcctInfo
  in
    Http.send resultToMsg request


type alias GetMatchingAccts msg = String -> (Result Http.Error MatchingAcctInfo -> msg) -> Cmd msg
getMatchingAccts: Flags -> GetMatchingAccts msg
getMatchingAccts flags flexId resultToMsg =
  let
    url = flags.matchingAcctsUrl++"?format=json"  -- Easier than an "Accept" header.
      |> replaceAll {oldSub="FLEXID", newSub=flexId}
    request = Http.get url decodeMatchingAcctInfo
  in
    Http.send resultToMsg request

-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

logVisitEvent : Flags
  -> Int
  -> VisitEventType
  -> Maybe ReasonForVisit  -- Only for Arrivals
  -> (Result Http.Error GenericResult -> msg)
  -> Cmd msg
logVisitEvent flags memberPK eventType reason resultToMsg =
  let
    eventVal = case eventType of
      Arrival -> "A"
      Present -> "P"
      Departure -> "D"
    reasonVal = case reason of
      Just Curiousity -> "CUR"
      Just ClassParticipant -> "CLS"
      Just MemberPrivileges -> "MEM"
      Just ClubPrivileges -> "CLB"
      Just GuestOfMember -> "GST"
      Just Volunteer -> "VOL"
      Just Other -> "OTH"
      Nothing -> "NUN"
    params = String.concat ["/", (toString memberPK), "_", eventVal, "_", reasonVal, "/"]
    url = flags.logVisitEventUrl++"?format=json"  -- Easier than an "Accept" header.
      |> replaceAll {oldSub="/12345_A_OTH/", newSub=params}
    request = Http.request
      { method = "GET"
      , headers = [authenticationHeader (DRF.Token flags.uniqueKioskId)]
      , url = url
      , body = Http.emptyBody
      , expect = Http.expectJson decodeGenericResult
      , timeout = Nothing
      , withCredentials = False
      }
  in
    Http.send resultToMsg request

type alias LogArrivalEvent msg = Int -> ReasonForVisit -> (Result Http.Error GenericResult -> msg) -> Cmd msg
logArrivalEvent : Flags -> LogArrivalEvent msg
logArrivalEvent flags memberPK reason resultToMsg =
  logVisitEvent flags memberPK Arrival (Just reason) resultToMsg

type alias LogDepartureEvent msg = Int -> (Result Http.Error GenericResult -> msg) -> Cmd msg
logDepartureEvent : Flags -> LogDepartureEvent msg
logDepartureEvent flags memberPK resultToMsg =
  logVisitEvent flags memberPK Departure Nothing resultToMsg

-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

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



-----------------------------------------------------------------------------
-- JSON
-----------------------------------------------------------------------------

decodeMatchingAcct : Dec.Decoder MatchingAcct
decodeMatchingAcct =
  Dec.map2 MatchingAcct
    (Dec.field "userName" Dec.string)
    (Dec.field "memberNum" Dec.int)

decodeMatchingAcctInfo : Dec.Decoder MatchingAcctInfo
decodeMatchingAcctInfo =
  Dec.map2 MatchingAcctInfo
    (Dec.field "target" Dec.string)
    (Dec.field "matches" (Dec.list decodeMatchingAcct))

decodeGenericResult : Dec.Decoder GenericResult
decodeGenericResult =
  Dec.map GenericResult
    (Dec.field "result" Dec.string)
