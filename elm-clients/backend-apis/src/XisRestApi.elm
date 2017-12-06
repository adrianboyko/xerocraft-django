module XisRestApi
  exposing
    ( createSession  -- Instantiate an API session
    , Claim
    , ClaimStatus (..)
    , ClaimListFilter (..)
    , Member
    , Membership
    , MemberListFilter (..)
    , MembershipListFilter (..)
    , Session
    , Task
    , TaskListFilter (..)
    , TaskPriority (..)
    , TimeBlock
    , TimeBlockType
    , Work
    , WorkListFilter (..)
    )

-- Standard
import Http
import Json.Encode as Enc
import Json.Encode.Extra as EncX
import Json.Decode as Dec exposing (maybe)
import Json.Decode.Extra as DecX
import Json.Decode.Pipeline exposing (decode, required, optional)
import List
import Regex exposing (regex)
import String
import Task exposing (Task)
import Time exposing (Time, hour, minute, second)

-- Third party
import List.Extra as ListX

-- Local
import DjangoRestFramework as DRF exposing (..)
import MembersApi as MembersApi  -- TODO: MembersApi will be replace with this REST api.
import ClockTime exposing (ClockTime)
import Duration exposing (Duration)
import CalendarDate exposing (CalendarDate)
import PointInTime exposing (PointInTime)
import RangeOfTime exposing (RangeOfTime)

-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------

staffingStatus_STAFFED = "S"  -- As defined in Django backend.

taskHighPriorityValue = "H"  -- As defined in Django backend.
taskMediumPriorityValue = "M"  -- As defined in Django backend.
taskLowPriorityValue = "L"  -- As defined in Django backend.


-----------------------------------------------------------------------------
-- GENERAL TYPES
-----------------------------------------------------------------------------

type alias XisRestFlags a =
  { a
  | claimListUrl : ResourceListUrl
  , discoveryMethodsUrl : ResourceListUrl
  , memberListUrl : ResourceListUrl
  , membershipListUrl : ResourceListUrl
  , taskListUrl : ResourceListUrl
  , timeBlocksUrl : ResourceListUrl
  , timeBlockTypesUrl : ResourceListUrl
  , uniqueKioskId : String
  , workListUrl : ResourceListUrl
  }

type alias ResourceGetterById res msg =
  Int -> (Result Http.Error res -> msg) -> Cmd msg

type alias ResourceGetterFromUrl res msg =
  ResourceUrl -> (Result Http.Error res -> msg) -> Cmd msg

type alias ResourcePutter res msg =
  res -> (Result Http.Error res -> msg) -> Cmd msg

type alias ResourcePoster res msg =
  res -> (Result Http.Error res -> msg) -> Cmd msg

type alias ListGetter res msg =
  (Result Http.Error (PageOf res) -> msg) -> Cmd msg

type alias FilteredListGetter filter res msg =
  List filter -> (Result Http.Error (PageOf res) -> msg) -> Cmd msg


-----------------------------------------------------------------------------
-- API INSTANCE
-----------------------------------------------------------------------------

-- REVIEW: Instead of get, post, etc, how about Using DRF's "action" names?
-- They are: list, create, retrieve, update, partial_update, destroy.
-- How about: list, create, retrieve, replace, patch, destroy?

type alias Session msg =
  { claimUrl : Int -> ResourceUrl
  , coverTime : List Membership -> Time -> Bool
  , defaultBlockType : List TimeBlockType -> Maybe TimeBlockType
  , getBlocksTypes : TimeBlock -> List TimeBlockType -> List TimeBlockType
  , getClaimList : FilteredListGetter ClaimListFilter Claim msg
  , getDiscoveryMethodList : ListGetter DiscoveryMethod msg
  , getMemberList : FilteredListGetter MemberListFilter Member msg
  , getMembershipById : ResourceGetterById Membership msg
  , getMembershipList : FilteredListGetter MembershipListFilter Membership msg
  , getTaskList : FilteredListGetter TaskListFilter Task msg
  , getTaskById : ResourceGetterById Task msg
  , getTaskFromUrl : ResourceGetterFromUrl Task msg
  , getTimeBlockList : ListGetter TimeBlock msg
  , getTimeBlockTypeList : ListGetter TimeBlockType msg
  , getWorkList : FilteredListGetter WorkListFilter Work msg
  , memberCanClaimTask : Int -> Task -> Bool
  , memberHasStatusOnTask : Int -> ClaimStatus -> Task -> Bool
  , membersClaimOnTask : Int -> Task -> Maybe Claim
  , membersStatusOnTask : Int -> Task -> Maybe ClaimStatus
  , memberUrl : Int -> ResourceUrl
  , mostRecentMembership : List Membership -> Maybe Membership
  , postClaim : ResourcePoster Claim msg
  , postWork : ResourcePoster Work msg
  , putClaim : ResourcePutter Claim msg
  , putWork : ResourcePutter Work msg
  , putWorkWithHeaders : List Http.Header -> ResourcePutter Work msg
  , taskUrl : Int -> ResourceUrl
  , workUrl : Int -> ResourceUrl
  }

createSession : XisRestFlags a -> Session msg
createSession flags =
  { claimUrl = urlFromId flags.claimListUrl
  , coverTime = coverTime
  , defaultBlockType = defaultBlockType
  , getBlocksTypes = getBlocksTypes
  , getClaimList = getClaimList flags
  , getDiscoveryMethodList = getDiscoveryMethodList flags
  , getMemberList = getMemberList flags
  , getMembershipById = getMembershipById flags
  , getMembershipList = getMembershipList flags
  , getTaskList = getTaskList flags
  , getTaskById = getTaskById flags
  , getTaskFromUrl = getTaskFromUrl flags
  , getTimeBlockList = getTimeBlockList flags
  , getTimeBlockTypeList = getTimeBlockTypeList flags
  , getWorkList = getWorkList flags
  , memberCanClaimTask = memberCanClaimTask flags
  , memberHasStatusOnTask = memberHasStatusOnTask flags
  , membersClaimOnTask = membersClaimOnTask flags
  , membersStatusOnTask = membersStatusOnTask flags
  , memberUrl = urlFromId flags.memberListUrl
  , mostRecentMembership = mostRecentMembership
  , postClaim = postClaim flags
  , postWork = postWork flags
  , putClaim = putClaim flags
  , putWork = putWorkWithHeaders flags []
  , putWorkWithHeaders = putWorkWithHeaders flags
  , taskUrl = urlFromId flags.taskListUrl
  , workUrl = urlFromId flags.workListUrl
  }


-----------------------------------------------------------------------------
-- TASKS
-----------------------------------------------------------------------------

type TaskPriority = HighPriority | MediumPriority | LowPriority


type alias Task =
  { claimSet : List Claim
  , creationDate : CalendarDate
  , deadline : Maybe CalendarDate
  , eligibleClaimants : List ResourceUrl
  , id : Int
  , instructions : String
  , isFullyClaimed : Bool
  , maxWork : Duration
  , maxWorkers : Int
  , owner : Maybe ResourceUrl
  , priority : TaskPriority
  , reviewer : Maybe ResourceUrl
  , scheduledDate : CalendarDate
  , shortDesc : String
  , shouldNag : Bool
  , status : String
  , workDuration : Maybe Duration
  , workStartTime : Maybe ClockTime
  }


type TaskListFilter
  = ScheduledDateEquals CalendarDate
  -- | ScheduledDateInRange Date Date
  -- | WorkStartTimeRange ClockTime ClockTime


taskListFilterToString : TaskListFilter -> String
taskListFilterToString filter =
  case filter of
    ScheduledDateEquals d -> "scheduled_date=" ++ (CalendarDate.toString d)


getTaskList : XisRestFlags a -> FilteredListGetter TaskListFilter Task msg
getTaskList flags filters resultToMsg =
  let
    request = httpGetRequest
      flags.uniqueKioskId
      (filteredListUrl flags.taskListUrl filters taskListFilterToString)
      (decodePageOf decodeTask)
  in
    Http.send resultToMsg request


getTaskById : XisRestFlags a -> ResourceGetterById Task msg
getTaskById flags taskNum resultToMsg =
  let url = urlFromId flags.taskListUrl taskNum
  in getTaskFromUrl flags url resultToMsg


getTaskFromUrl : XisRestFlags a -> ResourceGetterFromUrl Task msg
getTaskFromUrl flags url resultToMsg =
  let
    request = httpGetRequest flags.uniqueKioskId url decodeTask
  in
    Http.send resultToMsg request


--putTask : XisRestFlags a -> ResourcePutter Task msg
--putTask flags task resultToMsg =
--  let
--    request = Http.request
--      { method = "PUT"
--      , headers = [authenticationHeader flags.uniqueKioskId]
--      , url = urlFromId flags.taskListUrl task.id
--      , body = task |> encodeTask |> Http.jsonBody
--      , expect = Http.expectJson decodeTask
--      , timeout = Nothing
--      , withCredentials = False
--      }
--  in
--    Http.send resultToMsg request


memberCanClaimTask : XisRestFlags a -> Int -> Task -> Bool
memberCanClaimTask flags memberNum task =
  let
    url = urlFromId flags.memberListUrl memberNum
    memberIsEligible = List.member url task.eligibleClaimants
    canClaim = memberIsEligible && (not task.isFullyClaimed)
    alreadyClaimed = memberHasStatusOnTask flags memberNum CurrentClaimStatus task
  in
    canClaim || alreadyClaimed


membersClaimOnTask : XisRestFlags a -> Int -> Task -> Maybe Claim
membersClaimOnTask flags memberNum task =
  let
    memberUrl = urlFromId flags.memberListUrl memberNum
    isMembersClaim c = c.claimingMember == memberUrl
  in
    ListX.find isMembersClaim task.claimSet


membersStatusOnTask : XisRestFlags a -> Int -> Task -> Maybe ClaimStatus
membersStatusOnTask flags memberNum task =
  let
    membersClaim = membersClaimOnTask flags memberNum task
  in
    Maybe.map .status membersClaim


memberHasStatusOnTask : XisRestFlags a -> Int -> ClaimStatus -> Task -> Bool
memberHasStatusOnTask flags memberNum questionedStatus task =
  let
    actualStatus = membersStatusOnTask flags memberNum task
  in
    case actualStatus of
      Nothing -> False
      Just s -> s == questionedStatus


decodeTask : Dec.Decoder Task
decodeTask =
  decode Task
    |> required "claim_set" (Dec.list decodeClaim)
    |> required "creation_date" DRF.decodeCalendarDate
    |> required "deadline" (Dec.maybe DRF.decodeCalendarDate)
    |> required "eligible_claimants" (Dec.list decodeResourceUrl)
    |> required "id" Dec.int
    |> required "instructions" Dec.string
    |> required "is_fully_claimed" Dec.bool
    |> required "max_work" DRF.decodeDuration
    |> required "max_workers" Dec.int
    |> required "owner" (Dec.maybe decodeResourceUrl)
    |> required "priority" taskPriorityDecoder
    |> required "reviewer" (Dec.maybe decodeResourceUrl)
    |> required "scheduled_date" DRF.decodeCalendarDate
    |> required "short_desc" Dec.string
    |> required "should_nag" Dec.bool
    |> required "status" Dec.string
    |> required "work_duration" (Dec.maybe DRF.decodeDuration)
    |> required "work_start_time" (Dec.maybe DRF.decodeClockTime)


taskPriorityDecoder : Dec.Decoder TaskPriority
taskPriorityDecoder =
  Dec.string |> Dec.andThen
    ( \str ->
      case str of
        "H" -> Dec.succeed HighPriority
        "M" -> Dec.succeed MediumPriority
        "L" -> Dec.succeed LowPriority
        other -> Dec.fail <| "Unknown priority: " ++ other
    )


-----------------------------------------------------------------------------
-- CLAIMS
-----------------------------------------------------------------------------

type alias Claim =
  { claimedDuration : Duration
  , claimedStartTime : Maybe ClockTime
  , claimedTask : ResourceUrl
  , claimingMember : ResourceUrl
  , dateVerified : Maybe CalendarDate
  , id : Int
  , status : ClaimStatus
  , workSet : List ResourceUrl
  }


type ClaimStatus -- Per tasks.models.Claim in Python backend.
  = AbandonedClaimStatus
  | CurrentClaimStatus
  | DoneClaimStatus
  | ExpiredClaimStatus
  | QueuedClaimStatus
  | UninterestedClaimStatus
  | WorkingClaimStatus


claimStatusValue status =  -- Per tasks.models.Claim in Python backend.
  case status of
    AbandonedClaimStatus -> "A"
    CurrentClaimStatus -> "C"
    DoneClaimStatus -> "D"
    ExpiredClaimStatus -> "X"
    QueuedClaimStatus -> "Q"
    UninterestedClaimStatus -> "U"
    WorkingClaimStatus -> "W"


type ClaimListFilter
  = ClaimStatusEquals ClaimStatus
  | ClaimingMemberEquals Int
  | ClaimedTaskEquals Int


claimListFilterToString : ClaimListFilter -> String
claimListFilterToString filter =
  case filter of
    ClaimStatusEquals stat -> "status=" ++ (claimStatusValue stat)
    ClaimingMemberEquals membNum -> "claiming_member=" ++ (toString membNum)
    ClaimedTaskEquals taskNum -> "claimed_task=" ++ (toString taskNum)


getClaimList : XisRestFlags a -> FilteredListGetter ClaimListFilter Claim msg
getClaimList flags filters resultToMsg =
  let
    request = httpGetRequest
      flags.uniqueKioskId
      (filteredListUrl flags.claimListUrl filters claimListFilterToString)
      (decodePageOf decodeClaim)
  in
    Http.send resultToMsg request


decodeClaim : Dec.Decoder Claim
decodeClaim =
  decode Claim
    |> required "claimed_duration" DRF.decodeDuration
    |> required "claimed_start_time" (Dec.maybe DRF.decodeClockTime)
    |> required "claimed_task" decodeResourceUrl
    |> required "claiming_member" decodeResourceUrl
    |> required "date_verified" (Dec.maybe DRF.decodeCalendarDate)
    |> required "id" Dec.int
    |> required "status" decodeClaimStatus
    |> required "work_set" (Dec.list decodeResourceUrl)


decodeClaimStatus : Dec.Decoder ClaimStatus
decodeClaimStatus =
  Dec.string |> Dec.andThen
    ( \str ->
      case str of
        "A" -> Dec.succeed AbandonedClaimStatus
        "C" -> Dec.succeed CurrentClaimStatus
        "D" -> Dec.succeed DoneClaimStatus
        "X" -> Dec.succeed ExpiredClaimStatus
        "Q" -> Dec.succeed QueuedClaimStatus
        "U" -> Dec.succeed UninterestedClaimStatus
        "W" -> Dec.succeed WorkingClaimStatus
        other -> Dec.fail <| "Unknown claim status: " ++ other
    )


encodeClaimStatus : ClaimStatus -> Enc.Value
encodeClaimStatus status =
  case status of
    AbandonedClaimStatus -> Enc.string "A"
    CurrentClaimStatus -> Enc.string "C"
    DoneClaimStatus -> Enc.string "D"
    ExpiredClaimStatus -> Enc.string "X"
    QueuedClaimStatus -> Enc.string "Q"
    UninterestedClaimStatus -> Enc.string "U"
    WorkingClaimStatus -> Enc.string "W"


encodeClaim : Claim -> Enc.Value
encodeClaim claim =
  Enc.object
    [ ( "claiming_member", claim.claimingMember |> Enc.string )
    , ( "claimed_task", claim.claimedTask |> Enc.string )
    , ( "claimed_start_time", claim.claimedStartTime |> (EncX.maybe encodeClockTime))
    , ( "claimed_duration", claim.claimedDuration |> encodeDuration)
    , ( "status", claim.status |> encodeClaimStatus )
    , ( "date_verified", claim.dateVerified |> (EncX.maybe encodeCalendarDate))
    ]


putClaim : XisRestFlags a -> ResourcePutter Claim msg
putClaim flags claim resultToMsg =
  let
    request = Http.request
      { method = "PUT"
      , headers = [authenticationHeader flags.uniqueKioskId]
      , url = urlFromId flags.claimListUrl claim.id
      , body = claim |> encodeClaim |> Http.jsonBody
      , expect = Http.expectJson decodeClaim
      , timeout = Nothing
      , withCredentials = False
      }
  in
    Http.send resultToMsg request


postClaim : XisRestFlags a -> ResourcePutter Claim msg
postClaim flags claim resultToMsg =
  let
    request = Http.request
      { method = "POST"
      , headers = [authenticationHeader flags.uniqueKioskId]
      , url = flags.claimListUrl
      , body = claim |> encodeClaim |> Http.jsonBody
      , expect = Http.expectJson decodeClaim
      , timeout = Nothing
      , withCredentials = False
      }
  in
    Http.send resultToMsg request


-----------------------------------------------------------------------------
-- WORKS
-----------------------------------------------------------------------------

type alias Work =
  { claim: ResourceUrl
  , id : Int
  , witness : Maybe ResourceUrl
  , workDate : CalendarDate
  , workDuration : Maybe Duration
  , workStartTime : Maybe ClockTime
  }


{-| WorkPatch (used for partial updates) is the same as Work but all fields other than id are optional -}
type alias WorkPatch =
  { claim: Maybe ResourceUrl
  , id : Int
  , witness : Maybe ResourceUrl
  , workDate : Maybe CalendarDate
  , workDuration : Maybe Duration
  , workStartTime : Maybe ClockTime
  }


type WorkListFilter
  = WorkedClaimEquals Int
  | WorkDurationIsNull Bool


workListFilterToString : WorkListFilter -> String
workListFilterToString filter =
  case filter of
    WorkedClaimEquals id -> "claim=" ++ (toString id)
    WorkDurationIsNull setting -> "work_duration__isnull=" ++ (setting |> toString |> String.toLower)


getWorkList : XisRestFlags a -> FilteredListGetter WorkListFilter Work msg
getWorkList flags filters resultToMsg =
  let
    request = httpGetRequest
      flags.uniqueKioskId
      (filteredListUrl flags.workListUrl filters workListFilterToString)
      (decodePageOf decodeWork)
  in
    Http.send resultToMsg request


postWork : XisRestFlags a -> ResourcePutter Work msg
postWork flags work resultToMsg =
  let
    request = Http.request
      { method = "POST"
      , headers = [authenticationHeader flags.uniqueKioskId]
      , url = flags.workListUrl
      , body = work |> encodeWork |> Http.jsonBody
      , expect = Http.expectJson decodeWork
      , timeout = Nothing
      , withCredentials = False
      }
  in
    Http.send resultToMsg request


-- If "witness" is provided, the witness's password needs to be in an X-Witness-PW header.
putWorkWithHeaders : XisRestFlags a -> List Http.Header -> ResourcePutter Work msg
putWorkWithHeaders flags headers work resultToMsg =
  let
    request = Http.request
      { method = "PUT"
      , headers = headers ++ [authenticationHeader flags.uniqueKioskId]
      , url = urlFromId flags.workListUrl work.id
      , body = work |> encodeWork |> Http.jsonBody
      , expect = Http.expectJson decodeWork
      , timeout = Nothing
      , withCredentials = False
      }
  in
    Http.send resultToMsg request


encodeWork : Work -> Enc.Value
encodeWork work =
  Enc.object
    [ ( "claim", work.claim |> Enc.string )
    , ( "witness", work.witness |> (EncX.maybe Enc.string))
    , ( "work_date", work.workDate |> DRF.encodeCalendarDate)
    , ( "work_duration", work.workDuration |> (EncX.maybe DRF.encodeDuration))
    , ( "work_start_time", work.workStartTime |> (EncX.maybe DRF.encodeClockTime))
    ]


decodeWork : Dec.Decoder Work
decodeWork =
  decode Work
    |> required "claim" decodeResourceUrl
    |> required "id" Dec.int
    |> required "witness" (Dec.maybe DRF.decodeResourceUrl)
    |> required "work_date" DRF.decodeCalendarDate
    |> required "work_duration" (Dec.maybe DRF.decodeDuration)
    |> required "work_start_time" (Dec.maybe DRF.decodeClockTime)


-----------------------------------------------------------------------------
-- MEMBER
-----------------------------------------------------------------------------

type alias Member =
  { email : Maybe String
  , firstName : Maybe String
  , friendlyName : Maybe String  -- Read only
  , id : Int
  , isActive : Bool
  , isCurrentlyPaid : Bool  -- Read only
  , lastName : Maybe String
  , latestNonfutureMembership : Maybe Membership  -- Read only
  , userName : String
  }


type MemberListFilter
  = RfidNumberEquals Int
  | UsernameEquals String


memberListFilterToString : MemberListFilter -> String
memberListFilterToString filter =
  case filter of
    RfidNumberEquals n -> "rfidnum=" ++ (toString n)
    UsernameEquals s -> "auth_user__username=" ++ s


getMemberList : XisRestFlags a -> FilteredListGetter MemberListFilter Member msg
getMemberList flags filters resultToMsg =
  let
    request = httpGetRequest
      flags.uniqueKioskId
      (filteredListUrl flags.memberListUrl filters memberListFilterToString)
      (decodePageOf decodeMember)
  in
    Http.send resultToMsg request


decodeMember : Dec.Decoder Member
decodeMember =
  -- Note: email, first_name, and last_name might not be included in JSON, depending on permissions.
  decode Member
    |> optional "email" (Dec.maybe Dec.string) Nothing
    |> optional "first_name" (Dec.maybe Dec.string) Nothing
    |> required "friendly_name" (Dec.maybe Dec.string)
    |> required "id" Dec.int
    |> required "is_active" Dec.bool
    |> required "is_currently_paid" Dec.bool
    |> optional "last_name"  (Dec.maybe Dec.string) Nothing
    |> required "latest_nonfuture_membership" (Dec.maybe decodeMembership)
    |> required "username" Dec.string


-----------------------------------------------------------------------------
-- TIME BLOCK TYPES
-----------------------------------------------------------------------------

type alias TimeBlockType =
  { id : Int
  , name : String
  , description : String
  , isDefault : Bool
  }


getTimeBlockTypeList : XisRestFlags a -> ListGetter TimeBlockType msg
getTimeBlockTypeList model resultToMsg =
  let request = Http.get model.timeBlockTypesUrl (decodePageOf decodeTimeBlockType)
  in Http.send resultToMsg request


decodeTimeBlockType : Dec.Decoder TimeBlockType
decodeTimeBlockType =
  Dec.map4 TimeBlockType
    (Dec.field "id" Dec.int)
    (Dec.field "name" Dec.string)
    (Dec.field "description" Dec.string)
    (Dec.field "is_default" Dec.bool)


defaultBlockType : List TimeBlockType -> Maybe TimeBlockType
defaultBlockType allBlockTypes =
  List.filter .isDefault allBlockTypes |> List.head


-----------------------------------------------------------------------------
-- TIME BLOCKS
-----------------------------------------------------------------------------

type alias TimeBlock =
  { id : Int
  , isNow : Bool
  , startTime : String
  , duration : String
  , first : Bool
  , second : Bool
  , third : Bool
  , fourth : Bool
  , last : Bool
  , every : Bool
  , monday : Bool
  , tuesday : Bool
  , wednesday : Bool
  , thursday : Bool
  , friday : Bool
  , saturday : Bool
  , sunday : Bool
  , types : List String
  }


getTimeBlockList : XisRestFlags a -> ListGetter TimeBlock msg
getTimeBlockList model resultToMsg =
  let request = Http.get model.timeBlocksUrl (decodePageOf decodeTimeBlock)
  in Http.send resultToMsg request


decodeTimeBlock : Dec.Decoder TimeBlock
decodeTimeBlock =
  decode TimeBlock
    |> required "id" Dec.int
    |> required "is_now" Dec.bool
    |> required "start_time" Dec.string
    |> required "duration" Dec.string
    |> required "first" Dec.bool
    |> required "second" Dec.bool
    |> required "third" Dec.bool
    |> required "fourth" Dec.bool
    |> required "last" Dec.bool
    |> required "every" Dec.bool
    |> required "monday" Dec.bool
    |> required "tuesday" Dec.bool
    |> required "wednesday" Dec.bool
    |> required "thursday" Dec.bool
    |> required "friday" Dec.bool
    |> required "saturday" Dec.bool
    |> required "sunday" Dec.bool
    |> required "types" (Dec.list Dec.string)


getBlocksTypes : TimeBlock -> List TimeBlockType -> List TimeBlockType
getBlocksTypes specificBlock allBlockTypes =
  let
    relatedBlockTypeIds = List.map idFromUrl specificBlock.types
    isRelatedBlockType x = List.member (Ok x.id) relatedBlockTypeIds
  in
    List.filter isRelatedBlockType allBlockTypes


-----------------------------------------------------------------------------
-- MEMBERSHIPS
-----------------------------------------------------------------------------

type alias Membership =
  { id : Int
  , member : String
  , startDate : CalendarDate
  , endDate : CalendarDate
  , sale : Maybe Int  -- Memberships linked to group memberships don't have a sale.
  , sale_price : String
  , ctrlid : String
  , protected : Bool
  }


type MembershipListFilter
  = MembershipsWithMemberIdEqualTo Int


membershipListFilterToString : MembershipListFilter -> String
membershipListFilterToString filter =
  case filter of
    MembershipsWithMemberIdEqualTo id -> "member=" ++ (toString id)


getMembershipList : XisRestFlags a -> FilteredListGetter MembershipListFilter Membership msg
getMembershipList flags filters resultToMsg =
  let
    request = httpGetRequest
      flags.uniqueKioskId
      (filteredListUrl flags.membershipListUrl filters membershipListFilterToString)
      (decodePageOf decodeMembership)
  in
    Http.send resultToMsg request


getMembershipById : XisRestFlags a -> ResourceGetterById Membership msg
getMembershipById flags memberNum resultToMsg =
  let url = urlFromId flags.memberListUrl memberNum
  in getMembershipFromUrl flags url resultToMsg


getMembershipFromUrl : XisRestFlags a -> ResourceGetterFromUrl Membership msg
getMembershipFromUrl flags url resultToMsg =
  let
    request = httpGetRequest
      flags.uniqueKioskId
      url
      decodeMembership
  in
    Http.send resultToMsg request


decodeMembership : Dec.Decoder Membership
decodeMembership =
  decode Membership
    |> required "id" Dec.int
    |> required "member" Dec.string
    |> required "start_date" DRF.decodeCalendarDate
    |> required "end_date" DRF.decodeCalendarDate
    |> required "sale" (Dec.maybe Dec.int)
    |> required "sale_price" Dec.string
    |> required "ctrlid" Dec.string
    |> required "protected" Dec.bool

compareMembershipByEndDate : Membership -> Membership -> Order
compareMembershipByEndDate m1 m2 =
  CalendarDate.compare m1.endDate m2.endDate


mostRecentMembership : List Membership -> Maybe Membership
mostRecentMembership memberships =
  -- Note: The back-end is supposed to return memberships in reverse order by end-date
  -- REVIEW: This implementation does not assume ordered list from server, just to be safe.
  memberships |> List.sortWith compareMembershipByEndDate |> List.reverse |> List.head


{-| Determine whether the list of memberships covers the current time.
-}
coverTime : List Membership -> PointInTime -> Bool
coverTime memberships now =
  case mostRecentMembership memberships of
    Nothing ->
      False
    Just membership ->
      let
        membershipRange = RangeOfTime.fromCalendarDates membership.startDate membership.endDate
      in
        RangeOfTime.containsPoint membershipRange now


-----------------------------------------------------------------------------
-- DISCOVERY METHODS
-----------------------------------------------------------------------------

type alias DiscoveryMethod =
  { id : Int
  , name : String
  , order : Int
  , visible : Bool
  }


getDiscoveryMethodList : XisRestFlags a -> ListGetter DiscoveryMethod msg
getDiscoveryMethodList model resultToMsg =
  let request = Http.get model.discoveryMethodsUrl (decodePageOf decodeDiscoveryMethod)
  in Http.send resultToMsg request


decodeDiscoveryMethod : Dec.Decoder DiscoveryMethod
decodeDiscoveryMethod =
  decode DiscoveryMethod
    |> required "id" Dec.int
    |> required "name" Dec.string
    |> required "order" Dec.int
    |> required "visible" Dec.bool


-----------------------------------------------------------------------------
-- UTILITIES
-----------------------------------------------------------------------------

filteredListUrl : String -> List filter -> (filter -> String) -> ResourceListUrl
filteredListUrl listUrl filters filterToString =
  let
    filtersStr = case filters of
      [] -> ""
      _ -> "?" ++ (String.join "&" (List.map filterToString filters))
  in
    listUrl ++ filtersStr

