module MembersApi exposing
  ( createNewAcct
  , DiscoveryMethod
  , DiscoveryMethodInfo
  , djangoizeId
  , getDiscoveryMethods
  , getMatchingAccts
  , getCheckedInAccts
  , getRecentRfidEntries
  , getMemberships
  , logArrivalEvent
  , logDepartureEvent
  , setIsAdult
  , addDiscoveryMethods
  , MatchingAcct
  , MatchingAcctInfo
  , Membership
  , GenericResult
  , VisitEventType (..)
  , ReasonForVisit (..)
  , PageOfMemberships
  , mostRecentMembership
  , coverNow
  )

-- Standard
import Date as Date
import Date.Extra as DateX
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

djangoizeId : String -> String
djangoizeId rawId =
  -- Django allows alphanumeric, _, @, +, . and -.
  replaceAll {oldSub="[^-a-zA-Z0-9_@+.]", newSub="_"} rawId

replaceAll : {oldSub : String, newSub : String} -> String -> String
replaceAll {oldSub, newSub} whole =
  Regex.replace Regex.All (regex oldSub) (\_ -> newSub) whole

compareMembershipByEndDate : Membership -> Membership -> Order
compareMembershipByEndDate m1 m2 =
  DateX.compare m1.endDate m2.endDate

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

type alias DiscoveryMethod =
  { id : Int
  , name : String
  , order : Int
  , visible : Bool
  }

type alias DiscoveryMethodInfo =
  { count : Int
  , next : Maybe String
  , previous : Maybe String
  , results : List DiscoveryMethod
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
  | GuestOfMember
  | Volunteer
  | Other

type alias Membership =
  { id : Int
  , member : String
  , startDate : Date.Date
  , endDate : Date.Date
  , sale : Int
  , sale_price : String
  , ctrlid : String
  , protected : Bool
  }

type alias PageOfMemberships = PageOf Membership

-----------------------------------------------------------------------------
-- API
-----------------------------------------------------------------------------

getDiscoveryMethods : MembersApiModel a -> (Result Http.Error DiscoveryMethodInfo -> msg) -> Cmd msg
getDiscoveryMethods model resultToMsg =
  let request = Http.get model.discoveryMethodsUrl decodeDiscoveryMethodInfo
  in Http.send resultToMsg request

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


getMemberships : MembersApiModel a -> Int -> (Result Http.Error PageOfMemberships -> msg) -> Cmd msg
getMemberships flags memberNum resultToMsg =
  let
    placeHolder = "MEMBERNUM"
    urlPattern = "/members/api/memberships/?format=json&member="++placeHolder++"&ordering=-start_date"
    request = Http.request
      { method = "GET"
      , url = replaceAll {oldSub = placeHolder, newSub = toString memberNum} urlPattern
      , headers = [ authenticationHeader flags.uniqueKioskId ]
      , withCredentials = False
      , body = Http.emptyBody
      , timeout = Nothing
      , expect = Http.expectJson (decodePageOf decodeMembership)
      }
  in
    Http.send resultToMsg request


mostRecentMembership : List Membership -> Maybe Membership
mostRecentMembership memberships =
  -- Note: The back-end is supposed to return memberships in reverse order by end-date
  -- REVIEW: This implementation does not assume ordered list from server, just to be safe.
  memberships |> List.sortWith compareMembershipByEndDate |> List.reverse |> List.head


{-| Determine whether the list of memberships covers the current time.
-}
coverNow : List Membership -> Time -> Bool
coverNow memberships now =
  case mostRecentMembership memberships of
    Nothing ->
      False
    Just membership ->
      let endTime = Date.toTime membership.endDate
      in endTime >= now


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

decodeDiscoveryMethod : Dec.Decoder DiscoveryMethod
decodeDiscoveryMethod =
  decode DiscoveryMethod
    |> required "id" Dec.int
    |> required "name" Dec.string
    |> required "order" Dec.int
    |> required "visible" Dec.bool

decodeDiscoveryMethodInfo : Dec.Decoder DiscoveryMethodInfo
decodeDiscoveryMethodInfo =
  Dec.map4 DiscoveryMethodInfo
    (Dec.field "count" Dec.int)
    (Dec.field "next" (Dec.maybe Dec.string))
    (Dec.field "previous" (Dec.maybe Dec.string))
    (Dec.field "results" (Dec.list decodeDiscoveryMethod))

decodeGenericResult : Dec.Decoder GenericResult
decodeGenericResult =
  Dec.map GenericResult
    (Dec.field "result" Dec.string)

decodeMembership : Dec.Decoder Membership
decodeMembership =
  decode Membership
    |> required "id" Dec.int
    |> required "member" Dec.string
    |> required "start_date" DecX.date
    |> required "end_date" DecX.date
    |> required "sale" Dec.int
    |> required "sale_price" Dec.string
    |> required "ctrlid" Dec.string
    |> required "protected" Dec.bool
