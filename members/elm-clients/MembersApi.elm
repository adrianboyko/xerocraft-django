module MembersApi exposing
  ( createNewAcct
  , DiscoveryMethod
  , DiscoveryMethodInfo
  , djangoizeId
  , getDiscoveryMethods
  , getMatchingAccts
  , getCheckedInAccts
  , logVisitEvent
  , MatchingAcct
  , MatchingAcctInfo
  , GenericResult
  , VisitEventType (..)
  , ReasonForVisit (..)
  )

-- Standard
import Json.Decode as Dec
import Json.Encode as Enc
import Regex exposing (regex)
import Http

-- Third-Party
import Json.Decode.Pipeline exposing (decode, required, hardcoded)

-- Local

-----------------------------------------------------------------------------
-- UTILITIES
-----------------------------------------------------------------------------

djangoizeId : String -> String
djangoizeId rawId =
  -- Django allows alphanumeric, _, @, +, . and -.
  replaceAll "[^-a-zA-Z0-9_@+.]" "_" rawId

replaceAll : String -> String -> String -> String
replaceAll oldSub newSub theString =
  Regex.replace Regex.All (regex oldSub) (\_ -> newSub) theString

getDiscoveryMethods : {a|discoveryMethodsUrl:String} -> (Result Http.Error DiscoveryMethodInfo -> msg) -> Cmd msg
getDiscoveryMethods flags thing =
  let request = Http.get flags.discoveryMethodsUrl decodeDiscoveryMethodInfo
  in Http.send thing request

getCheckedInAccts: {a|checkedInAcctsUrl:String} -> (Result Http.Error MatchingAcctInfo -> msg) -> Cmd msg
getCheckedInAccts flags thing =
  let
    url = flags.checkedInAcctsUrl++"?format=json"  -- Easier than an "Accept" header.
    request = Http.get url decodeMatchingAcctInfo
  in
    Http.send thing request

getMatchingAccts: {a|matchingAcctsUrl:String} -> String -> (Result Http.Error MatchingAcctInfo -> msg) -> Cmd msg
getMatchingAccts flags flexId thing =
  let
    url = flags.matchingAcctsUrl++"?format=json"  -- Easier than an "Accept" header.
      |> replaceAll "FLEXID" flexId
    request = Http.get url decodeMatchingAcctInfo
  in
    Http.send thing request

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

logVisitEvent : {a|logVisitEventUrl:String}
  -> Int
  -> VisitEventType
  -> ReasonForVisit
  -> (Result Http.Error GenericResult -> msg)
  -> Cmd msg
logVisitEvent flags memberPK eventType reason thing =
  let
    eventVal = case eventType of
      Arrival -> "A"
      Present -> "P"
      Departure -> "D"
    reasonVal = case reason of
      Curiousity -> "CUR"
      ClassParticipant -> "CLS"
      MemberPrivileges -> "MEM"
      GuestOfMember -> "GST"
      Volunteer -> "VOL"
      Other -> "OTH"
    params = String.concat ["/", (toString memberPK), "_", eventVal, "_", reasonVal, "/"]
    url = flags.logVisitEventUrl++"?format=json"  -- Easier than an "Accept" header.
      |> replaceAll "/12345_A_OTH/" params
    request = Http.get url decodeGenericResult
  in
    Http.send thing request

createNewAcct : String -> String -> String -> String -> String -> (Result Http.Error String -> msg) -> Cmd msg
createNewAcct fullName userName email password signature thing =
  let
    url = "https://www.xerocraft.org/kfritz/checkinActions2.php"
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
      , url = url
      , body = Http.stringBody "application/x-www-form-urlencoded" formData
      , expect = Http.expectString
      , timeout = Nothing
      , withCredentials = False
      }
   in
     Http.send thing request

-----------------------------------------------------------------------------
-- TYPES
-----------------------------------------------------------------------------

type alias MatchingAcct =
  { userName: String
  , memberNum: Int
  }

type alias MatchingAcctInfo =
  { target: String
  , matches: List MatchingAcct
  }

type alias DiscoveryMethod =
  { id: Int
  , name: String
  , order: Int
  , visible: Bool
  , selected: Bool  -- This is a GUI field. Use extensible records to move this to scene?
  }

type alias DiscoveryMethodInfo =
  { count: Int
  , next: Maybe String
  , previous: Maybe String
  , results: List DiscoveryMethod
  }

type alias GenericResult =
  { result: String
  }

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
    |> hardcoded False

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
