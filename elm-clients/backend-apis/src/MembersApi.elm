module MembersApi exposing
  ( createNewAcct
  , getMatchingAccts
  , getCheckedInAccts
  , getRecentRfidEntries
  , logArrivalEvent
  , logDepartureEvent
  , setIsAdult
  , addDiscoveryMethods
  , MatchingAcct
  , MatchingAcctInfo
  , GenericResult
  , VisitEventType (..)
  , ReasonForVisit (..)
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
import DjangoRestFramework exposing (PageOf, decodePageOf, authenticationHeader)


-----------------------------------------------------------------------------
-- UTILITIES
-----------------------------------------------------------------------------

replaceAll : {oldSub : String, newSub : String} -> String -> String
replaceAll {oldSub, newSub} whole =
  Regex.replace Regex.All (regex oldSub) (\_ -> newSub) whole

-----------------------------------------------------------------------------
-- API TYPES
-----------------------------------------------------------------------------

type alias MembersApiModel a =
  { a
  | addDiscoveryMethodUrl : String
  , checkedInAcctsUrl : String
  , csrfToken : String
  , discoveryMethodsUrl : String
  , logVisitEventUrl : String
  , matchingAcctsUrl : String
  , recentRfidEntriesUrl : String
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

getCheckedInAccts: MembersApiModel a -> (Result Http.Error MatchingAcctInfo -> msg) -> Cmd msg
getCheckedInAccts flags resultToMsg =
  let
    url = flags.checkedInAcctsUrl++"?format=json"  -- Easier than an "Accept" header.
    request = Http.get url decodeMatchingAcctInfo
  in
    Http.send resultToMsg request

getRecentRfidEntries: MembersApiModel a -> (Result Http.Error MatchingAcctInfo -> msg) -> Cmd msg
getRecentRfidEntries flags resultToMsg =
  let
    url = flags.recentRfidEntriesUrl++"?format=json"  -- Easier than an "Accept" header.
    request = Http.get url decodeMatchingAcctInfo
  in
    Http.send resultToMsg request


getMatchingAccts: MembersApiModel a -> String -> (Result Http.Error MatchingAcctInfo -> msg) -> Cmd msg
getMatchingAccts flags flexId resultToMsg =
  let
    url = flags.matchingAcctsUrl++"?format=json"  -- Easier than an "Accept" header.
      |> replaceAll {oldSub="FLEXID", newSub=flexId}
    request = Http.get url decodeMatchingAcctInfo
  in
    Http.send resultToMsg request

-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

logVisitEvent : MembersApiModel a
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
      , headers = [authenticationHeader flags.uniqueKioskId]
      , url = url
      , body = Http.emptyBody
      , expect = Http.expectJson decodeGenericResult
      , timeout = Nothing
      , withCredentials = False
      }
  in
    Http.send resultToMsg request

logArrivalEvent flags memberPK reason resultToMsg =
  logVisitEvent flags memberPK Arrival (Just reason) resultToMsg

logDepartureEvent flags memberPK resultToMsg =
  logVisitEvent flags memberPK Departure Nothing resultToMsg

-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

createNewAcct : MembersApiModel a -> String -> String -> String -> String -> String -> (Result Http.Error String -> msg) -> Cmd msg
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

setIsAdult : MembersApiModel a -> String -> String -> Bool -> (Result Http.Error String -> msg) -> Cmd msg
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

addDiscoveryMethods : MembersApiModel a -> String -> String -> List Int -> (Result Http.Error String -> msg) -> Cmd msg
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
