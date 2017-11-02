module XisRestApi
  exposing
    ( Claim
    , ClaimStatus (..)
    , ClaimListFilter (..)
    , Task
    , TaskListFilter (..)
    , TaskPriority (..)
    , getClaimList
    , getMemberUrl
    , getTaskList
    , memberCanClaimTask
    )

-- Standard
import Date exposing (Date)
import Http
import Json.Encode as Enc
import Json.Decode as Dec exposing (maybe)
import Json.Decode.Extra as DecX
import Json.Decode.Pipeline exposing (decode, required)
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
  , isoDateStrFromDate
  , resourceUrlDecoder
  )


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
  , taskListUrl : ResourceListUrl
  , uniqueKioskId : String
  , workListUrl : ResourceListUrl
  }


-----------------------------------------------------------------------------
-- MEMBERS
-----------------------------------------------------------------------------

getMemberUrl : XisRestFlags a -> Int -> ResourceUrl
getMemberUrl flags memberNum =
  flags.memberListUrl ++ (toString memberNum) ++ "/"


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


getTaskListUrl : XisRestFlags a -> Maybe (List TaskListFilter) -> ResourceListUrl
getTaskListUrl flags filters =
  let
    filterStr = case filters of
      Nothing -> ""
      Just fs -> "?" ++ (String.join "&" (List.map taskListFilterToString fs))
  in
    flags.taskListUrl ++ filterStr


getTaskList : XisRestFlags a -> Maybe (List TaskListFilter) -> (Result Http.Error (PageOf Task) -> msg) -> Cmd msg
getTaskList flags filters resultToMsg =
  let
    request = Http.request
      { method = "GET"
      , headers = [authenticationHeader flags.uniqueKioskId]
      , url = getTaskListUrl flags filters
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
    memberUrl = getMemberUrl flags memberNum
    memberIsEligible = List.member memberUrl task.eligibleClaimants
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


getClaimListUrl : XisRestFlags a -> Maybe (List ClaimListFilter) -> ResourceListUrl
getClaimListUrl flags filters =
  let
    filterStr = case filters of
      Nothing -> ""
      Just fs -> "?" ++ (String.join "&" (List.map claimListFilterToString fs))
  in
    flags.claimListUrl ++ filterStr


getClaimList : XisRestFlags a -> Maybe (List ClaimListFilter) -> (Result Http.Error (PageOf Claim) -> msg) -> Cmd msg
getClaimList flags filters resultToMsg =
  let
    request = Http.request
      { method = "GET"
      , headers = [authenticationHeader flags.uniqueKioskId]
      , url = getClaimListUrl flags filters
      , body = Http.emptyBody
      , expect = Http.expectJson (decodePageOf decodeClaim)
      , timeout = Nothing
      , withCredentials = False
      }
  in
    Http.send resultToMsg request


--getClaim : XisRestFlags -> Int -> Task
--getClaim flags taskId =


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

