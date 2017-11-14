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
    )

-- Standard
import Date exposing (Date)
import Date.Extra as DateX
import Http
import Json.Encode as Enc
import Json.Decode as Dec exposing (maybe)
import Json.Decode.Extra as DecX
import Json.Decode.Pipeline exposing (decode, required, optional)
import List
import Regex exposing (regex)
import String
import Task exposing (Task)
import Time exposing (Time, hour, minute, second)

-- Third party

-- Local
import DjangoRestFramework as DRF exposing
  ( PageOf
  , ClockTime
  , Duration
  , ResourceUrl
  , ResourceListUrl
  , authenticationHeader
  , decodePageOf
  , getIdFromUrl
  , isoDateStrFromDate
  , resourceUrlDecoder
  )
import MembersApi as MembersApi  -- TODO: MembersApi will be replace with this REST api.

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
  , memberListUrl : ResourceListUrl
  , membershipListUrl : ResourceListUrl
  , taskListUrl : ResourceListUrl
  , timeBlocksUrl : ResourceListUrl
  , timeBlockTypesUrl : ResourceListUrl
  , uniqueKioskId : String
  , workListUrl : ResourceListUrl
  }


-----------------------------------------------------------------------------
-- API INSTANCE
-----------------------------------------------------------------------------

type alias ResourceGetter item msg =
  Int -> (Result Http.Error (PageOf item) -> msg) -> Cmd msg

type alias ListGetter item msg =
  (Result Http.Error (PageOf item) -> msg) -> Cmd msg

type alias FilteredListGetter filter item msg =
  Maybe (List filter) -> (Result Http.Error (PageOf item) -> msg) -> Cmd msg

type alias Session msg =
  { coverTime : List Membership -> Time -> Bool
  , defaultBlockType : List TimeBlockType -> Maybe TimeBlockType
  , getBlocksTypes : TimeBlock -> List TimeBlockType -> List TimeBlockType
  , getClaimList : FilteredListGetter ClaimListFilter Claim msg
  , getMemberList : FilteredListGetter MemberListFilter Member msg
  , getMembership : ResourceGetter Membership msg
  , getMembershipList : FilteredListGetter MembershipListFilter Membership msg
  , getTaskList : FilteredListGetter TaskListFilter Task msg
  , getTimeBlockList : ListGetter TimeBlock msg
  , getTimeBlockTypeList : ListGetter TimeBlockType msg
  , memberCanClaimTask : Int -> Task -> Bool
  , memberUrl : Int -> ResourceUrl
  , mostRecentMembership : List Membership -> Maybe Membership
  }

createSession : XisRestFlags a -> Session msg
createSession flags =
  { coverTime = coverTime
  , defaultBlockType = defaultBlockType
  , getBlocksTypes = getBlocksTypes
  , getClaimList = getClaimList flags
  , getMemberList = getMemberList flags
  , getMembership = getMembership flags
  , getMembershipList = getMembershipList flags
  , getTaskList = getTaskList flags
  , getTimeBlockList = getTimeBlockList flags
  , getTimeBlockTypeList = getTimeBlockTypeList flags
  , memberCanClaimTask = memberCanClaimTask flags
  , memberUrl = resourceUrl flags.memberListUrl
  , mostRecentMembership = mostRecentMembership
  }


-----------------------------------------------------------------------------
-- TASKS
-----------------------------------------------------------------------------

type TaskPriority = HighPriority | MediumPriority | LowPriority


type alias Task =
  { claimants : List ResourceUrl
  , claimSet : List ResourceUrl
  , creationDate : Date
  , deadline : Maybe Date
  , eligibleClaimants : List ResourceUrl
  , id : Int
  , instructions : String
  , isFullyClaimed : Bool
  , maxWork : Duration
  , maxWorkers : Int
  , owner : Maybe ResourceUrl
  , priority : TaskPriority
  , reviewer : Maybe ResourceUrl
  , scheduledDate : Date
  , shortDesc : String
  , shouldNag : Bool
  , status : String
  , workDuration : Maybe Duration
  , workStartTime : Maybe ClockTime
  }


type TaskListFilter
  = ScheduledDateEquals Date
  -- | ScheduledDateInRange Date Date
  -- | WorkStartTimeRange ClockTime ClockTime


taskListFilterToString : TaskListFilter -> String
taskListFilterToString filter =
  case filter of
    ScheduledDateEquals d -> "scheduled_date=" ++ (isoDateStrFromDate d)


getTaskUrl : XisRestFlags a -> Int -> ResourceUrl
getTaskUrl flags taskNum =
  flags.taskListUrl ++ "/" ++ (toString taskNum) ++ "/"


getTaskList : XisRestFlags a -> FilteredListGetter TaskListFilter Task msg
getTaskList flags filters resultToMsg =
  let
    request = Http.request
      { method = "GET"
      , headers = [authenticationHeader flags.uniqueKioskId]
      , url = filteredListUrl flags.taskListUrl filters taskListFilterToString
      , body = Http.emptyBody
      , expect = Http.expectJson (decodePageOf decodeTask)
      , timeout = Nothing
      , withCredentials = False
      }
  in
    Http.send resultToMsg request


--getTask : XisRestFlags -> Int -> Task
--getTask flags taskId =

-- NOTE: This will return False if member has ALREADY claimed the task.
memberCanClaimTask : XisRestFlags a -> Int -> Task -> Bool
memberCanClaimTask flags memberNum task =
  let
    url = resourceUrl flags.memberListUrl memberNum
    memberIsEligible = List.member url task.eligibleClaimants
  in
    memberIsEligible && (not task.isFullyClaimed)

decodeTask : Dec.Decoder Task
decodeTask =
  decode Task
    |> required "claimants" (Dec.list resourceUrlDecoder)
    |> required "claim_set" (Dec.list resourceUrlDecoder)
    |> required "creation_date" DecX.date
    |> required "deadline" (Dec.maybe DecX.date)
    |> required "eligible_claimants" (Dec.list resourceUrlDecoder)
    |> required "id" Dec.int
    |> required "instructions" Dec.string
    |> required "is_fully_claimed" Dec.bool
    |> required "max_work" DRF.durationDecoder
    |> required "max_workers" Dec.int
    |> required "owner" (Dec.maybe resourceUrlDecoder)
    |> required "priority" taskPriorityDecoder
    |> required "reviewer" (Dec.maybe resourceUrlDecoder)
    |> required "scheduled_date" DecX.date
    |> required "short_desc" Dec.string
    |> required "should_nag" Dec.bool
    |> required "status" Dec.string
    |> required "work_duration" (Dec.maybe DRF.durationDecoder)
    |> required "work_start_time" (Dec.maybe DRF.clockTimeDecoder)


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
  , dateVerified : Maybe Date
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


getClaimUrl : XisRestFlags a -> Int -> ResourceUrl
getClaimUrl flags claimNum =
  flags.claimListUrl ++ "/" ++ (toString claimNum) ++ "/"


getClaimList : XisRestFlags a -> FilteredListGetter ClaimListFilter Claim msg
getClaimList flags filters resultToMsg =
  let
    request = Http.request
      { method = "GET"
      , headers = [authenticationHeader flags.uniqueKioskId]
      , url = filteredListUrl flags.claimListUrl filters claimListFilterToString
      , body = Http.emptyBody
      , expect = Http.expectJson (decodePageOf decodeClaim)
      , timeout = Nothing
      , withCredentials = False
      }
  in
    Http.send resultToMsg request


decodeClaim : Dec.Decoder Claim
decodeClaim =
  decode Claim
    |> required "claimed_duration" DRF.durationDecoder
    |> required "claimed_start_time" (Dec.maybe DRF.clockTimeDecoder)
    |> required "claimed_task" resourceUrlDecoder
    |> required "claiming_member" resourceUrlDecoder
    |> required "date_verified" (Dec.maybe DecX.date)
    |> required "id" Dec.int
    |> required "status" decodeClaimStatus
    |> required "work_set" (Dec.list resourceUrlDecoder)


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


-----------------------------------------------------------------------------
-- WORKS
-----------------------------------------------------------------------------

type alias Work = {}


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


memberListFilterToString : MemberListFilter -> String
memberListFilterToString filter =
  case filter of
    RfidNumberEquals n -> "rfidnum=" ++ (toString n)


getMemberList : XisRestFlags a -> FilteredListGetter MemberListFilter Member msg
getMemberList flags filters resultToMsg =
  let
    request = Http.request
      { method = "GET"
      , headers = [authenticationHeader flags.uniqueKioskId]
      , url = filteredListUrl flags.memberListUrl filters memberListFilterToString
      , body = Http.emptyBody
      , expect = Http.expectJson (decodePageOf decodeMember)
      , timeout = Nothing
      , withCredentials = False
      }
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
    relatedBlockTypeIds = List.map getIdFromUrl specificBlock.types
    isRelatedBlockType x = List.member (Ok x.id) relatedBlockTypeIds
  in
    List.filter isRelatedBlockType allBlockTypes


-----------------------------------------------------------------------------
-- MEMBERSHIPS
-----------------------------------------------------------------------------

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

type MembershipListFilter
  = MembershipsWithMemberIdEqualTo Int


membershipListFilterToString : MembershipListFilter -> String
membershipListFilterToString filter =
  case filter of
    MembershipsWithMemberIdEqualTo id -> "member=" ++ (toString id)


getMembershipList : XisRestFlags a -> FilteredListGetter MembershipListFilter Membership msg
getMembershipList flags filters resultToMsg =
  let
    request = Http.request
      { method = "GET"
      , headers = [authenticationHeader flags.uniqueKioskId]
      , url = filteredListUrl flags.membershipListUrl filters membershipListFilterToString
      , body = Http.emptyBody
      , expect = Http.expectJson (decodePageOf decodeMembership)
      , timeout = Nothing
      , withCredentials = False
      }
  in
    Http.send resultToMsg request


getMembership : XisRestFlags a -> ResourceGetter Membership msg
getMembership flags memberNum resultToMsg =
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

compareMembershipByEndDate : Membership -> Membership -> Order
compareMembershipByEndDate m1 m2 =
  DateX.compare m1.endDate m2.endDate

mostRecentMembership : List Membership -> Maybe Membership
mostRecentMembership memberships =
  -- Note: The back-end is supposed to return memberships in reverse order by end-date
  -- REVIEW: This implementation does not assume ordered list from server, just to be safe.
  memberships |> List.sortWith compareMembershipByEndDate |> List.reverse |> List.head


{-| Determine whether the list of memberships covers the current time.
-}
coverTime : List Membership -> Time -> Bool
coverTime memberships now =
  case mostRecentMembership memberships of
    Nothing ->
      False
    Just membership ->
      let endTime = Date.toTime membership.endDate
      in endTime >= now


-----------------------------------------------------------------------------
-- UTILITIES
-----------------------------------------------------------------------------

filteredListUrl : String -> Maybe (List filter) -> (filter -> String) -> ResourceListUrl
filteredListUrl listUrl filters filterToString =
  let
    filtersStr = case filters of
      Nothing -> ""
      Just fs -> "?" ++ (String.join "&" (List.map filterToString fs))
  in
    listUrl ++ filtersStr

resourceUrl : String -> Int -> ResourceListUrl
resourceUrl listUrl id =
  listUrl ++ "/" ++ (toString id) ++ "/"

replaceAll : {oldSub : String, newSub : String} -> String -> String
replaceAll {oldSub, newSub} whole =
  Regex.replace Regex.All (regex oldSub) (\_ -> newSub) whole
