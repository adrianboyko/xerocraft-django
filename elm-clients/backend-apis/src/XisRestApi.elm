module XisRestApi
  exposing
    ( createSession  -- Instantiate an API session
    , djangoizeId
    , setClaimsDateVerified
    , setClaimsStatus
    , setPlaysDuration
    , setWorksDuration
    , setWorksWitness
    --------------------
    , AuthenticationResult
    , Broadcast, BroadcastData, BroadcastFilter(..), BroadcastType(..)
    , Claim, ClaimData
    , ClaimStatus (..)
    , ClaimFilter (..)
    , DiscoveryMethod, DiscoveryMethodData
    , LogLevel (..)
    , EpisodeTrack, EpisodeTrackData
    , Member, MemberData
    , Membership, MembershipData
    , MemberFilter (..)
    , MembershipFilter (..)
    , NowPlaying
    , Play, PlayData, PlayFilter (..)
    , Session
    , Show, ShowData
    , Episode, EpisodeData, EpisodeFilter (..)
    , Task, StaffingStatus(..), TaskData
    , TaskFilter (..)
    , TaskPriority (..)
    , TimeBlock, TimeBlockData
    , TimeBlockType, TimeBlockTypeData
    , TrackBroadcast, TrackBroadcastData
    , TrackData
    , VendLog, VendLogData
    , VisitEvent, VisitEventDataOut
    , VisitEventType(..), VisitEventReason(..), VisitEventFilter(..), VisitEventMethod(..)
    , Work, WorkData, WorkFilter (..)
    , WorkNote, WorkNoteData
    , XisRestFlags
    )

-- Standard
import Http
import Json.Encode as Enc
import Json.Encode.Extra as EncX
import Json.Decode as Dec
import Json.Decode.Extra as DecX
import Json.Decode.Pipeline exposing (decode, required, optional)
import List
import Regex exposing (regex)
import String
import Task exposing (Task)
import Date exposing (Day(..))

-- Third party
import List.Extra as ListX

-- Local
import DjangoRestFramework as DRF exposing (..)
import ClockTime exposing (ClockTime)
import Duration exposing (Duration)
import CalendarDate exposing (CalendarDate)
import PointInTime exposing (PointInTime)
import RangeOfTime

-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- GENERAL TYPES
-----------------------------------------------------------------------------

type alias XisRestFlags =
  { authenticateUrl : ServiceUrl
  , broadcastListUrl : ResourceListUrl
  , claimListUrl : ResourceListUrl
  , discoveryMethodListUrl : ResourceListUrl
  , emailMembershipInfoUrl : ServiceUrl
  , episodeListUrl: ResourceListUrl
  , episodeTrackListUrl : ResourceListUrl
  , logMessageUrl : ServiceUrl  -- This logs a message on the server side.
  , memberListUrl : ResourceListUrl
  , membershipListUrl : ResourceListUrl
  , nowPlayingUrl : ServiceUrl
  , playListUrl : ResourceListUrl  -- Tasks
  , productListUrl : ResourceListUrl
  , showListUrl : ResourceListUrl
  , taskListUrl : ResourceListUrl
  , timeBlockListUrl : ResourceListUrl
  , timeBlockTypeListUrl : ResourceListUrl
  , trackBroadcastListUrl : ResourceListUrl
  , trackListUrl : ResourceListUrl
  , vendLogListUrl : ResourceListUrl
  , visitEventListUrl : ResourceListUrl
  , workListUrl : ResourceListUrl
  , workNoteListUrl : ResourceListUrl
  }


-----------------------------------------------------------------------------
-- API INSTANCE
-----------------------------------------------------------------------------

-- REVIEW: Instead of get, post, etc, how about Using DRF's "action" names?
-- They are: list, create, retrieve, update, partial_update, destroy.
-- How about: list, create, retrieve, replace, patch, destroy?

type alias Session msg =

  ----- RESOURCE GETTERS -----
  -- TODO: Getters should use "filters", like list filters. E.g. "ById" and "FromUrl"
  { getMembershipById : GetterById Membership msg
  , getPlayByUrl : GetterFromUrl Play msg
  , getTaskById : GetterById Task msg
  , getTaskFromUrl : GetterFromUrl Task msg
  , getWorkFromUrl : GetterFromUrl Work msg

  ----- RESOURCE CREATORS -----
  , createBroadcast : Creator BroadcastData Broadcast msg
  , createClaim : Creator ClaimData Claim msg
  , createEpisodeTrack : Creator EpisodeTrackData EpisodeTrack msg
  , createPlay : Creator PlayData Play msg
  , createEpisode : Creator EpisodeData Episode msg
  , createTrackBroadcast : Creator TrackBroadcastData TrackBroadcast msg
  , createVendLog : Creator VendLogData VendLog msg
  , createVisitEvent : Creator VisitEventDataOut VisitEvent msg
  , createWork : Creator WorkData Work msg
  , createWorkNote : Creator WorkNoteData WorkNote msg

  ----- RESOURCE DELETERS -----
  , deleteEpisodeTrackById : DeleterById msg
  , deleteEpisodeTrackByUrl : DeleterByUrl msg
  , deletePlayById : DeleterById msg
  , deletePlayByUrl : DeleterByUrl msg
  , deleteWorkById : DeleterById msg
  , deleteWorkByUrl : DeleterByUrl msg

  ----- RESOURCE LISTERS -----
  , listBroadcasts : FilteringLister BroadcastFilter Broadcast msg
  , listClaims : FilteringLister ClaimFilter Claim msg
  , listDiscoveryMethods : Lister DiscoveryMethod msg
  , listEpisodes : FilteringLister EpisodeFilter Episode msg
  , listMembers : FilteringLister MemberFilter Member msg
  , listMemberships : FilteringLister MembershipFilter Membership msg
  , listPlays : FilteringLister PlayFilter Play msg
  , listShows : Lister Show msg
  , listTasks : FilteringLister TaskFilter Task msg
  , listTimeBlocks : Lister TimeBlock msg
  , listTimeBlockTypes : Lister TimeBlockType msg
  , listVisitEvents : FilteringLister VisitEventFilter VisitEvent msg
  , listWorks : FilteringLister WorkFilter Work msg
  , moreVisitEvents : ListPager VisitEvent msg

  ----- RESOURCE REPLACERS
  , replaceClaim : Replacer Claim msg
  , replaceEpisodeTrack : Replacer EpisodeTrack msg
  , replaceWork : Replacer Work msg
  , replacePlay : Replacer Play msg
  , replaceEpisode : Replacer Episode msg

  ----- RESOURCE URLS -----
  , broadcastUrl : Int -> ResourceUrl
  , claimUrl : Int -> ResourceUrl
  , episodeUrl : Int -> ResourceUrl
  , episodeTrackUrl : Int -> ResourceUrl
  , memberUrl : Int -> ResourceUrl
  , productUrl : Int  -> ResourceUrl
  , showUrl : Int -> ResourceUrl
  , taskUrl : Int -> ResourceUrl
  , trackBroadcastUrl : Int -> ResourceUrl
  , vendLogUrl : Int -> ResourceUrl
  , visitEventUrl : Int -> ResourceUrl
  , workUrl : Int -> ResourceUrl
  , workNoteUrl : Int -> ResourceUrl

  ----- OTHER -----
  , authenticate: String -> String -> (Result Http.Error AuthenticationResult -> msg) -> Cmd msg
  , blockHasType : String -> List TimeBlockType -> TimeBlock -> Bool
  , coverTime : List Membership -> PointInTime -> Bool
  , defaultBlockType : List TimeBlockType -> Maybe TimeBlockType
  , emailMembershipInfo : EmailMembershipInfo msg
  , logMessage : LogMessage msg
  , getBlocksTypes : TimeBlock -> List TimeBlockType -> List TimeBlockType
  , memberCanClaimTask : Int -> Task -> Bool
  , memberHasStatusOnTask : Int -> ClaimStatus -> Task -> Bool
  , membersClaimOnTask : Int -> Task -> Maybe Claim
  , membersStatusOnTask : Int -> Task -> Maybe ClaimStatus
  , membersWithStatusOnTask : ClaimStatus -> Task -> List ResourceUrl
  , mostRecentMembership : List Membership -> Maybe Membership
  , nowPlaying : (Result Http.Error NowPlaying -> msg) -> Cmd msg
  , pitInBlock : PointInTime -> TimeBlock -> Bool
  }

createSession : XisRestFlags -> Authorization -> Session msg
createSession flags auth =

  ----- RESOURCE GETTERS -----
  { getMembershipById = getResourceById auth flags.membershipListUrl decodeMembershipData
  , getPlayByUrl = getResourceFromUrl auth decodePlayData
  , getTaskById = getResourceById auth flags.taskListUrl decodeTaskData
  , getTaskFromUrl = getResourceFromUrl auth decodeTaskData
  , getWorkFromUrl = getResourceFromUrl auth decodeWorkData

  ----- RESOURCE CREATORS -----
  , createBroadcast = createResource auth flags.broadcastListUrl encodeBroadcastData decodeBroadcastData
  , createClaim = createResource auth flags.claimListUrl encodeClaimData decodeClaimData
  , createEpisodeTrack = createResource auth flags.episodeTrackListUrl encodeEpisodeTrackData decodeEpisodeTrackData
  , createPlay = createResource auth flags.playListUrl encodePlayData decodePlayData
  , createEpisode = createResource auth flags.episodeListUrl encodeEpisodeData decodeEpisodeData
  , createTrackBroadcast = createResource auth flags.trackBroadcastListUrl encodeTrackBroadcastData decodeTrackBroadcastData
  , createVendLog = createResource auth flags.vendLogListUrl encodeVendLogData decodeVendLogData
  , createVisitEvent = createVisitEvent auth flags.visitEventListUrl  -- REVIEW: Can this one be reconciled with other creators?
  , createWork = createResource auth flags.workListUrl encodeWorkData decodeWorkData
  , createWorkNote = createResource auth flags.workNoteListUrl encodeWorkNoteData decodeWorkNoteData

  ----- RESOURCE DELETERS -----
  , deleteEpisodeTrackById = deleteResourceById auth flags.episodeTrackListUrl
  , deleteEpisodeTrackByUrl = deleteResourceByUrl auth
  , deletePlayById = deleteResourceById auth flags.playListUrl
  , deletePlayByUrl = deleteResourceByUrl auth
  , deleteWorkById = deleteResourceById auth flags.workListUrl
  , deleteWorkByUrl = deleteResourceByUrl auth

  ----- RESOURCE LISTERS -----
  , listBroadcasts = listFilteredResources auth flags.broadcastListUrl decodeBroadcastData broadcastFilterToString
  , listClaims = listFilteredResources auth flags.claimListUrl decodeClaimData claimFilterToString
  , listDiscoveryMethods = listResources auth flags.discoveryMethodListUrl decodeDiscoveryMethodData
  , listEpisodes = listFilteredResources auth flags.episodeListUrl decodeEpisodeData episodeFilterToString
  , listMembers = listFilteredResources auth flags.memberListUrl decodeMemberData memberFilterToString
  , listMemberships = listFilteredResources auth flags.membershipListUrl decodeMembershipData membershipFilterToString
  , listPlays = listFilteredResources auth flags.playListUrl decodePlayData playFilterToString
  , listShows = listResources auth flags.showListUrl decodeShowData
  , listTasks = listFilteredResources auth flags.taskListUrl decodeTaskData taskFilterToString
  , listTimeBlocks = listResources auth flags.timeBlockListUrl decodeTimeBlockData
  , listTimeBlockTypes = listResources auth flags.timeBlockTypeListUrl decodeTimeBlockTypeData
  , listVisitEvents = listFilteredResources auth flags.visitEventListUrl decodeVisitEventDataIn visitEventFilterToString
  , listWorks = listFilteredResources auth flags.workListUrl decodeWorkData workFilterToString
  , moreVisitEvents = moreVisitEvents flags auth  -- TODO: Need a generic "moreResources"

  ----- RESOURCE REPLACERS -----
  , replaceClaim = replaceResource auth flags.claimListUrl encodeClaimData decodeClaimData
  , replaceEpisodeTrack = replaceResource auth flags.episodeTrackListUrl encodeEpisodeTrackData decodeEpisodeTrackData
  , replaceWork = replaceResource auth flags.workListUrl encodeWorkData decodeWorkData
  , replacePlay = replaceResource auth flags.playListUrl encodePlayData decodePlayData
  , replaceEpisode = replaceResource auth flags.episodeListUrl encodeEpisodeData decodeEpisodeData

  ----- RESOURCE URLS -----
  , broadcastUrl = urlFromId flags.broadcastListUrl
  , claimUrl = urlFromId flags.claimListUrl
  , episodeUrl = urlFromId flags.episodeListUrl
  , episodeTrackUrl = urlFromId flags.episodeTrackListUrl
  , memberUrl = urlFromId flags.memberListUrl
  , productUrl = urlFromId flags.productListUrl
  , showUrl = urlFromId flags.showListUrl
  , taskUrl = urlFromId flags.taskListUrl
  , trackBroadcastUrl = urlFromId flags.trackBroadcastListUrl
  , vendLogUrl = urlFromId flags.visitEventListUrl
  , visitEventUrl = urlFromId flags.visitEventListUrl
  , workUrl = urlFromId flags.workListUrl
  , workNoteUrl = urlFromId flags.workNoteListUrl

  ----- OTHER -----
  , authenticate = authenticate flags auth
  , blockHasType = blockHasType
  , coverTime = coverTime
  , defaultBlockType = defaultBlockType
  , emailMembershipInfo = emailMembershipInfo flags auth
  , logMessage = logMessage flags auth
  , getBlocksTypes = getBlocksTypes
  , memberCanClaimTask = memberCanClaimTask flags
  , memberHasStatusOnTask = memberHasStatusOnTask flags
  , membersClaimOnTask = membersClaimOnTask flags
  , membersStatusOnTask = membersStatusOnTask flags
  , membersWithStatusOnTask = membersWithStatusOnTask
  , mostRecentMembership = mostRecentMembership
  , nowPlaying = nowPlaying flags auth
  , pitInBlock = pitInBlock
  }


-----------------------------------------------------------------------------
-- TASKS
-----------------------------------------------------------------------------

type alias Task = Resource TaskData


type alias TaskData =
  { anybodyIsEligible : Bool
  , claimSet : List Claim
  , creationDate : CalendarDate
  , deadline : Maybe CalendarDate
  , eligibleClaimants : List ResourceUrl
  , instructions : String
  , isFullyClaimed : Bool
  , maxWork : Duration
  , maxWorkers : Int
  , nameOfLikelyWorker : Maybe String
  , owner : Maybe ResourceUrl
  , priority : TaskPriority
  , reviewer : Maybe ResourceUrl
  , scheduledDate : CalendarDate
  , shortDesc : String
  , shouldNag : Bool
  , staffingStatus : StaffingStatus
  , status : String  -- TODO: Change this to an enum type.
  , workDuration : Maybe Duration
  , workStartTime : Maybe ClockTime
  }


type TaskPriority = HighPriority | MediumPriority | LowPriority


type StaffingStatus = SS_Staffed | SS_Unstaffed | SS_Provisional | SS_Done


type TaskFilter
  = ScheduledDateEquals CalendarDate
  -- | ScheduledDateInRange Date Date
  -- | WorkStartTimeRange ClockTime ClockTime


taskFilterToString : TaskFilter -> String
taskFilterToString filter =
  case filter of
    ScheduledDateEquals d -> "scheduled_date=" ++ CalendarDate.toString d


memberCanClaimTask : XisRestFlags -> Int -> Task -> Bool
memberCanClaimTask flags memberNum task =
  let
    url = urlFromId flags.memberListUrl memberNum
    memberIsEligible = List.member url task.data.eligibleClaimants
    canClaim = memberIsEligible && (task.data.isFullyClaimed |> not)
    alreadyClaimed = memberHasStatusOnTask flags memberNum CurrentClaimStatus task
    abandonedClaim = memberHasStatusOnTask flags memberNum AbandonedClaimStatus task
  in
    canClaim || alreadyClaimed || abandonedClaim || task.data.anybodyIsEligible

--isFullyClaimed : Task -> Bool
--isFullyClaimed t = False  -- TODO: Implement
--staffingStatus : Task -> StaffingStatus
--staffingStatus t = SS_Staffed  -- TODO: Implement

membersClaimOnTask : XisRestFlags -> Int -> Task -> Maybe Claim
membersClaimOnTask flags memberNum task =
  let
    memberUrl = urlFromId flags.memberListUrl memberNum
    isMembersClaim c = c.data.claimingMember == memberUrl
  in
    ListX.find isMembersClaim task.data.claimSet


membersStatusOnTask : XisRestFlags -> Int -> Task -> Maybe ClaimStatus
membersStatusOnTask flags memberNum task =
  let
    membersClaim = membersClaimOnTask flags memberNum task
  in
    Maybe.map (.data >> .status) membersClaim


memberHasStatusOnTask : XisRestFlags -> Int -> ClaimStatus -> Task -> Bool
memberHasStatusOnTask flags memberNum questionedStatus task =
  let
    actualStatus = membersStatusOnTask flags memberNum task
  in
    case actualStatus of
      Nothing -> False
      Just s -> s == questionedStatus


membersWithStatusOnTask : ClaimStatus -> Task -> List ResourceUrl
membersWithStatusOnTask status task =
  let
    hasStatus claim = claim.data.status == status
    claimsWithStatus = List.filter hasStatus task.data.claimSet
  in
    List.map (.data >> .claimingMember) claimsWithStatus


decodeTaskData : Dec.Decoder TaskData
decodeTaskData =
  decode TaskData
    |> required "anybody_is_eligible" Dec.bool
    |> required "claim_set" (Dec.list (decodeResource decodeClaimData))
    |> required "creation_date" decodeCalendarDate
    |> required "deadline" (Dec.maybe decodeCalendarDate)
    |> required "eligible_claimants" (Dec.list decodeResourceUrl)
    |> required "instructions" Dec.string
    |> required "is_fully_claimed" Dec.bool
    |> required "max_work" decodeDuration
    |> required "max_workers" Dec.int
    |> required "name_of_likely_worker" (Dec.maybe Dec.string)
    |> required "owner" (Dec.maybe decodeResourceUrl)
    |> required "priority" taskPriorityDecoder
    |> required "reviewer" (Dec.maybe decodeResourceUrl)
    |> required "scheduled_date" decodeCalendarDate
    |> required "short_desc" Dec.string
    |> required "should_nag" Dec.bool
    |> required "staffing_status" staffingStatusDecoder
    |> required "status" Dec.string
    |> required "work_duration" (Dec.maybe decodeDuration)
    |> required "work_start_time" (Dec.maybe decodeClockTime)


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

staffingStatusDecoder : Dec.Decoder StaffingStatus
staffingStatusDecoder =
  Dec.string |> Dec.andThen
    ( \str ->
      case str of
        "S" -> Dec.succeed SS_Staffed
        "U" -> Dec.succeed SS_Unstaffed
        "P" -> Dec.succeed SS_Provisional
        "D" -> Dec.succeed SS_Done
        other -> Dec.fail <| "Unknown staffing status: " ++ other
    )


-----------------------------------------------------------------------------
-- CLAIMS
-----------------------------------------------------------------------------


type alias Claim = Resource ClaimData


type alias ClaimData =
  { claimedDuration : Duration
  , claimedStartTime : Maybe ClockTime
  , claimedTask : ResourceUrl
  , claimingMember : ResourceUrl
  , dateVerified : Maybe CalendarDate
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


type ClaimFilter
  = ClaimStatusEquals ClaimStatus
  | ClaimingMemberEquals Int
  | ClaimedTaskEquals Int


-- "Changing" nested records is awkward in Elm, so these "setters" are provided.

setClaimsDateVerified : Maybe CalendarDate -> Claim -> Claim
setClaimsDateVerified newSetting oldClaim =
  let
    data = oldClaim.data
    newData = {data | dateVerified = newSetting}
  in
    {oldClaim | data = newData}


setClaimsStatus : ClaimStatus -> Claim ->  Claim
setClaimsStatus newSetting oldClaim =
  let
    data = oldClaim.data
    newData = {data | status = newSetting}
  in
    {oldClaim | data = newData}


claimFilterToString : ClaimFilter -> String
claimFilterToString filter =
  case filter of
    ClaimStatusEquals stat -> "status=" ++ claimStatusValue stat
    ClaimingMemberEquals membNum -> "claiming_member=" ++ toString membNum
    ClaimedTaskEquals taskNum -> "claimed_task=" ++ toString taskNum


decodeClaimData : Dec.Decoder ClaimData
decodeClaimData =
  decode ClaimData
    |> required "claimed_duration" decodeDuration
    |> required "claimed_start_time" (Dec.maybe decodeClockTime)
    |> required "claimed_task" decodeResourceUrl
    |> required "claiming_member" decodeResourceUrl
    |> required "date_verified" (Dec.maybe decodeCalendarDate)
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


encodeClaimData : ClaimData -> Enc.Value
encodeClaimData = Enc.object << claimDataNVPs


claimDataNVPs : ClaimData -> List (String, Enc.Value)
claimDataNVPs cd =
  [ ( "claiming_member", cd.claimingMember |> Enc.string )
  , ( "claimed_task", cd.claimedTask |> Enc.string )
  , ( "claimed_start_time", cd.claimedStartTime |> EncX.maybe encodeClockTime)
  , ( "claimed_duration", cd.claimedDuration |> encodeDuration)
  , ( "status", cd.status |> encodeClaimStatus )
  , ( "date_verified", cd.dateVerified |> EncX.maybe encodeCalendarDate)
  ]


-----------------------------------------------------------------------------
-- WORK
-----------------------------------------------------------------------------

type alias Work = Resource WorkData


type alias WorkData =
  { claim: ResourceUrl
  , witness : Maybe ResourceUrl
  , workDate : CalendarDate
  , workDuration : Maybe Duration
  , workStartTime : Maybe ClockTime
  }


-- "Changing" nested records is awkward in Elm, so these "setters" are provided.

setWorksWitness : Maybe ResourceUrl -> Work ->  Work
setWorksWitness newSetting oldWork =
  let
    data = oldWork.data
    newData = {data | witness = newSetting}
  in
    {oldWork | data = newData}


setWorksDuration : Maybe Duration -> Work -> Work
setWorksDuration newSetting oldWork =
  let
    data = oldWork.data
    newData = {data | workDuration = newSetting}
  in
    {oldWork | data = newData}


type WorkFilter
  = WorkedClaimEquals Int
  | WorkDurationIsNull Bool


workFilterToString : WorkFilter -> String
workFilterToString filter =
  case filter of
    WorkedClaimEquals id -> "claim=" ++ toString id
    WorkDurationIsNull setting -> "work_duration__isnull=" ++ (setting |> toString |> String.toLower)


encodeWorkData : WorkData -> Enc.Value
encodeWorkData = Enc.object << workDataNVPs


workDataNVPs : WorkData -> List (String, Enc.Value)
workDataNVPs wd =
  [ ( "claim", wd.claim |> Enc.string )
  , ( "witness", wd.witness |> EncX.maybe Enc.string)
  , ( "work_date", wd.workDate |> encodeCalendarDate)
  , ( "work_duration", wd.workDuration |> EncX.maybe encodeDuration)
  , ( "work_start_time", wd.workStartTime |> EncX.maybe encodeClockTime)
  ]


decodeWorkData : Dec.Decoder WorkData
decodeWorkData =
  decode WorkData
    |> required "claim" decodeResourceUrl
    |> required "witness" (Dec.maybe decodeResourceUrl)
    |> required "work_date" decodeCalendarDate
    |> required "work_duration" (Dec.maybe decodeDuration)
    |> required "work_start_time" (Dec.maybe decodeClockTime)


-----------------------------------------------------------------------------
-- WORKERS
-----------------------------------------------------------------------------

type alias WorkerData =
  { member : ResourceUrl
  , shouldIncludeAlarms : Bool
  , shouldNag : Bool
  , shouldSendStatements : Bool
  , timeAcctBalance : Maybe Float
  }


type alias Worker = Resource WorkerData


decodeWorker : Dec.Decoder Worker
decodeWorker = decodeResource decodeWorkerData


decodeWorkerData : Dec.Decoder WorkerData
decodeWorkerData =
  decode WorkerData
    |> required "member" decodeResourceUrl
    |> required "should_include_alarms" Dec.bool
    |> required "should_nag" Dec.bool
    |> required "should_report_work_mtd" Dec.bool
    |> required "time_acct_balance" (Dec.maybe Dec.float)


-----------------------------------------------------------------------------
-- WORK NOTES
-----------------------------------------------------------------------------

type alias WorkNoteData =
  { author : Maybe ResourceUrl
  , content : String
  , work : ResourceUrl
  , whenWritten : PointInTime
  }


type alias WorkNote = Resource WorkNoteData


encodeWorkNoteData : WorkNoteData -> Enc.Value
encodeWorkNoteData = Enc.object << workNoteDataNVPs


{-| Name Value Pairs for WorkNoteData -}
workNoteDataNVPs : WorkNoteData -> List (String, Enc.Value)
workNoteDataNVPs wnd =
  [ ( "author", wnd.author |> EncX.maybe Enc.string)
  , ( "content", wnd.content |> Enc.string)
  , ( "work", wnd.work |> Enc.string)
  , ( "when_written", wnd.whenWritten |> PointInTime.isoString |> Enc.string)
  ]


decodeWorkNoteData : Dec.Decoder WorkNoteData
decodeWorkNoteData =
  decode WorkNoteData
    |> required "author" (Dec.maybe decodeResourceUrl)
    |> required "content" Dec.string
    |> required "work" decodeResourceUrl
    |> required "when_written" (Dec.string |> Dec.andThen (PointInTime.fromString >> DecX.fromResult))


-----------------------------------------------------------------------------
-- PLAY (FROM TASKS)
-----------------------------------------------------------------------------

type alias PlayData =
  { playingMember : ResourceUrl
  , playDate : CalendarDate
  , playDuration : Maybe Duration
  , playStartTime : Maybe ClockTime
  }


type alias Play = Resource PlayData


-- "Changing" nested records is awkward in Elm, so these "setters" are provided.
setPlaysDuration : Maybe Duration -> Play -> Play
setPlaysDuration newSetting oldPlay =
  let
    data = oldPlay.data
    newData = {data | playDuration = newSetting}
  in
    {oldPlay | data = newData}


type PlayFilter
  = PlayDurationIsNull Bool
  | PlayingMemberEquals Int
  | PlayDateEquals CalendarDate


playFilterToString : PlayFilter -> String
playFilterToString filter =
  case filter of
    PlayDurationIsNull setting -> "play_duration__isnull=" ++ (setting |> toString |> String.toLower)
    PlayingMemberEquals id ->  "playing_member=" ++ toString id
    PlayDateEquals d -> "play_date=" ++ CalendarDate.toString d


listPlays : XisRestFlags -> Authorization -> FilteringLister PlayFilter Play msg
listPlays flags auth  filters resultToMsg =
  let
    request = getRequest
      auth
      (filteredListUrl flags.playListUrl filters playFilterToString)
      (decodePageOf (decodeResource decodePlayData))
  in
    Http.send resultToMsg request


encodePlayData : PlayData -> Enc.Value
encodePlayData = Enc.object << playDataNVPs


playDataNVPs : PlayData -> List (String, Enc.Value)
playDataNVPs pd =
  [ ( "playing_member", pd.playingMember |> Enc.string)
  , ( "play_date", pd.playDate |> encodeCalendarDate)
  , ( "play_duration", pd.playDuration |> EncX.maybe encodeDuration)
  , ( "play_start_time", pd.playStartTime |> EncX.maybe encodeClockTime)
  ]


decodePlayData : Dec.Decoder PlayData
decodePlayData =
  decode PlayData
    |> required "playing_member" decodeResourceUrl
    |> required "play_date" decodeCalendarDate
    |> required "play_duration" (Dec.maybe decodeDuration)
    |> required "play_start_time" (Dec.maybe decodeClockTime)


-----------------------------------------------------------------------------
-- MEMBER
-----------------------------------------------------------------------------

type alias Member = Resource MemberData


type alias MemberData =
  { email : Maybe String
  , firstName : Maybe String
  , friendlyName : String  -- Read only
  , isActive : Bool
  , isCurrentlyPaid : Bool  -- Read only
  , lastName : Maybe String
  , latestNonfutureMembership : Maybe Membership  -- Read only
  , userName : String
  , worker : Worker  -- Read only
  }


type MemberFilter
  = RfidNumberEquals Int
  | EmailEquals String
  | UsernameEquals String
  | UsernameContains String
  | UsernameStartsWith String
  | LastNameStartsWith String
  | LastNameEquals String
  | IsActive Bool


memberFilterToString : MemberFilter -> String
memberFilterToString filter =
  case filter of
    RfidNumberEquals n -> "rfidnum=" ++ toString n
    EmailEquals s -> "auth_user__email__iexact=" ++ s
    UsernameEquals s -> "auth_user__username__iexact=" ++ s
    UsernameContains s -> "auth_user__username__icontains=" ++ s
    UsernameStartsWith s -> "auth_user__username__istartswith=" ++ s
    LastNameStartsWith s -> "auth_user__last_name__istartswith=" ++ s
    LastNameEquals s -> "auth_user__last_name__iexact=" ++ s
    IsActive b -> "auth_user__is_active=" ++ (if b then "1" else "0")


decodeMemberData : Dec.Decoder MemberData
decodeMemberData =
  -- Note: email, first_name, and last_name might not be included in JSON, depending on permissions.
  decode MemberData
    |> optional "email" (Dec.maybe Dec.string) Nothing
    |> optional "first_name" (Dec.maybe Dec.string) Nothing
    |> required "friendly_name" Dec.string
    |> required "is_active" Dec.bool
    |> required "is_currently_paid" Dec.bool
    |> optional "last_name"  (Dec.maybe Dec.string) Nothing
    |> required "latest_nonfuture_membership" (Dec.maybe (decodeResource decodeMembershipData))
    |> required "username" Dec.string
    |> required "worker" decodeWorker


-----------------------------------------------------------------------------
-- TIME BLOCK TYPES
-----------------------------------------------------------------------------

type alias TimeBlockType = Resource TimeBlockTypeData


type alias TimeBlockTypeData =
  { name : String
  , description : String
  , isDefault : Bool
  }


decodeTimeBlockTypeData : Dec.Decoder TimeBlockTypeData
decodeTimeBlockTypeData =
  Dec.map3 TimeBlockTypeData
    (Dec.field "name" Dec.string)
    (Dec.field "description" Dec.string)
    (Dec.field "is_default" Dec.bool)


defaultBlockType : List TimeBlockType -> Maybe TimeBlockType
defaultBlockType allBlockTypes =
  List.filter (.data >> .isDefault) allBlockTypes |> List.head


-----------------------------------------------------------------------------
-- TIME BLOCKS
-----------------------------------------------------------------------------

type alias TimeBlock = Resource TimeBlockData


type alias TimeBlockData =
  { startTime : ClockTime
  , duration : Duration
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


decodeTimeBlockData : Dec.Decoder TimeBlockData
decodeTimeBlockData =
  decode TimeBlockData
    |> required "start_time" decodeClockTime
    |> required "duration" decodeDuration
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
    relatedBlockTypeIds = List.map idFromUrl specificBlock.data.types
    isRelatedBlockType x = List.member (Ok x.id) relatedBlockTypeIds
  in
    List.filter isRelatedBlockType allBlockTypes


blockHasType : String -> List TimeBlockType -> TimeBlock -> Bool
blockHasType typeName allBlockTypes block =
  let
    blocksTypes = getBlocksTypes block allBlockTypes
  in
    List.member typeName (List.map (.data >> .name) blocksTypes)


pitInBlock : PointInTime -> TimeBlock -> Bool
pitInBlock pit block =
  let
    bd = block.data
    _ = if bd.last then Debug.crash "The 'last xday' case is not yet supported" else "OK"

    year = PointInTime.year pit
    month = PointInTime.month pit
    dayOfMonth = PointInTime.dayOfMonth pit
    calendarDate = CalendarDate year month dayOfMonth

    actualNth = (PointInTime.dayOfMonth pit) // 7 + 1
    actualDoW = PointInTime.dayOfWeek pit
    actualToD = ClockTime.fromTime pit

    nthMatch  -- nth of month
      = bd.every
      || bd.first && actualNth == 1
      || bd.second && actualNth == 2
      || bd.third && actualNth == 3
      || bd.fourth && actualNth == 4

    dowMatch -- day of week
      = bd.monday && actualDoW == Mon
      || bd.tuesday && actualDoW == Tue
      || bd.wednesday && actualDoW == Wed
      || bd.thursday && actualDoW == Thu
      || bd.friday && actualDoW == Fri
      || bd.saturday && actualDoW == Sat
      || bd.sunday && actualDoW == Sun

    startPit = PointInTime.fromCalendarDateAndClockTime calendarDate bd.startTime
    lateEnough = startPit <= pit
    earlyEnough = pit <= startPit+bd.duration

  in
    nthMatch && dowMatch && lateEnough && earlyEnough


-----------------------------------------------------------------------------
-- MEMBERSHIPS
-----------------------------------------------------------------------------

type alias Membership = Resource MembershipData


type alias MembershipData =
  { member : String
  , startDate : CalendarDate
  , endDate : CalendarDate
  , sale : Maybe Int  -- Memberships linked to group memberships don't have a sale.
  , sale_price : String
  , ctrlid : String
  , protected : Bool
  }


type MembershipFilter
  = MembershipsWithMemberIdEqualTo Int


membershipFilterToString : MembershipFilter -> String
membershipFilterToString filter =
  case filter of
    MembershipsWithMemberIdEqualTo id -> "member=" ++ toString id


decodeMembershipData : Dec.Decoder MembershipData
decodeMembershipData =
  decode MembershipData
    |> required "member" Dec.string
    |> required "start_date" decodeCalendarDate
    |> required "end_date" decodeCalendarDate
    |> required "sale" (Dec.maybe Dec.int)
    |> required "sale_price" Dec.string
    |> required "ctrlid" Dec.string
    |> required "protected" Dec.bool


compareMembershipByEndDate : Membership -> Membership -> Order
compareMembershipByEndDate m1 m2 =
  CalendarDate.compare m1.data.endDate m2.data.endDate


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
        membershipRange =
          RangeOfTime.fromCalendarDates membership.data.startDate membership.data.endDate
      in
        RangeOfTime.containsPoint membershipRange now


-----------------------------------------------------------------------------
-- DISCOVERY METHODS
-----------------------------------------------------------------------------

type alias DiscoveryMethod = Resource DiscoveryMethodData


type alias DiscoveryMethodData =
  { name : String
  , order : Int
  , visible : Bool
  }


decodeDiscoveryMethod : Dec.Decoder DiscoveryMethod
decodeDiscoveryMethod = decodeResource decodeDiscoveryMethodData

decodeDiscoveryMethodData : Dec.Decoder DiscoveryMethodData
decodeDiscoveryMethodData =
  decode DiscoveryMethodData
    |> required "name" Dec.string
    |> required "order" Dec.int
    |> required "visible" Dec.bool


-----------------------------------------------------------------------------
-- VEND LOG (SODA)
-----------------------------------------------------------------------------

type alias VendLog = Resource VendLogData


type alias VendLogData =
  { whoFor : ResourceUrl
  , when : PointInTime
  , product : ResourceUrl
  }


encodeVendLogData : VendLogData -> Enc.Value
encodeVendLogData = Enc.object << vendLogDataNVPs


vendLogDataNVPs : VendLogData -> List (String, Enc.Value)
vendLogDataNVPs log =
  [ ( "who_for", log.whoFor |> Enc.string)
  , ( "when", log.when |> encodePointInTime )
  , ( "product", log.product |> Enc.string )
  ]


decodeVendLogData : Dec.Decoder VendLogData
decodeVendLogData =
  decode VendLogData
    |> required "who_for" decodeResourceUrl
    |> required "when" decodePointInTime
    |> required "product" decodeResourceUrl



-----------------------------------------------------------------------------
-- VISIT EVENTS
-----------------------------------------------------------------------------

type alias VisitEvent = Resource VisitEventDataIn


type alias VisitEventDataIn =
  { who : Member
  , when : PointInTime
  , eventType : VisitEventType
  , reason : Maybe VisitEventReason
  , method : VisitEventMethod
  }

type alias VisitEventDataOut =
  { who : ResourceUrl
  , when : PointInTime
  , eventType : VisitEventType
  , reason : Maybe VisitEventReason
  , method : VisitEventMethod
  }


encodeVisitEventDataOut : VisitEventDataOut -> Enc.Value
encodeVisitEventDataOut = Enc.object << visitEventDataNVPs


visitEventDataNVPs : VisitEventDataOut -> List (String, Enc.Value)
visitEventDataNVPs ved =
  [ ( "who", ved.who |> Enc.string)
  , ( "when", ved.when |> encodePointInTime )
  , ( "event_type", ved.eventType |> eventTypeString |> Enc.string )
  , ( "reason", ved.reason |> Maybe.map eventReasonString |> EncX.maybe Enc.string )
  , ( "method", ved.method |> eventMethodString |> Enc.string )
  ]


type VisitEventMethod
  = VEM_Rfid
  | VEM_FrontDesk
  | VEM_MobileApp
  | VEM_Unknown


type VisitEventReason
  = VER_Class
  | VER_Club
  | VER_Curious
  | VER_Guest
  | VER_Member
  | VER_Other
  | VER_PublicAccess
  | VER_Volunteer


type VisitEventType
  = VET_Arrival  -- REVIEW: Should try to make "reason" an argument of this constructor?
  | VET_Present
  | VET_Departure


eventTypeString : VisitEventType -> String
eventTypeString x =
  case x of
    VET_Arrival -> "A"
    VET_Departure -> "D"
    VET_Present -> "P"


eventMethodString : VisitEventMethod -> String
eventMethodString x =
  case x of
    VEM_Rfid -> "R"
    VEM_FrontDesk -> "F"
    VEM_MobileApp -> "M"
    VEM_Unknown -> "U"


eventReasonString : VisitEventReason -> String
eventReasonString x =
  case x of
    VER_Class -> "CLS"
    VER_Club -> "CLB"
    VER_Curious -> "CUR"
    VER_Guest -> "GST"
    VER_Member -> "MEM"
    VER_PublicAccess -> "PUB"
    VER_Other -> "OTH"
    VER_Volunteer -> "VOL"


type VisitEventFilter
  = VEF_WhenGreaterOrEquals PointInTime
  | VEF_EventTypeEquals VisitEventType
  | VEF_EventMethodEquals VisitEventMethod


visitEventFilterToString : VisitEventFilter -> String
visitEventFilterToString filter =
  case filter of
    VEF_WhenGreaterOrEquals pit -> "when__gte=" ++ (PointInTime.isoString pit)
    VEF_EventTypeEquals vet -> "event_type=" ++ eventTypeString(vet)
    VEF_EventMethodEquals meth -> "method=" ++ eventMethodString(meth)


moreVisitEvents : XisRestFlags -> Authorization -> ListPager VisitEvent msg
moreVisitEvents flags auth pageUrl resultToMsg =
  let
    request = getRequest auth pageUrl (decodePageOf (decodeResource decodeVisitEventDataIn))
  in
    Http.send resultToMsg request


createVisitEvent : Authorization -> ResourceUrl -> Creator VisitEventDataOut VisitEvent msg
createVisitEvent auth listUrl visitEventData resultToMsg =
  let
    request = Http.request
      { method = "POST"
      , headers = [authenticationHeader auth]
      , url = listUrl
      , body = visitEventData |> visitEventDataNVPs |> Enc.object |> Http.jsonBody
      , expect = Http.expectJson decodeVisitEvent
      , timeout = Nothing
      , withCredentials = False
      }
  in
    Http.send resultToMsg request


decodeVisitEvent : Dec.Decoder VisitEvent
decodeVisitEvent = decodeResource decodeVisitEventDataIn


decodeVisitEventDataIn : Dec.Decoder VisitEventDataIn
decodeVisitEventDataIn =
  decode VisitEventDataIn
    |> required "who_embed" (decodeResource decodeMemberData)
    |> required "when" decodePointInTime
    |> required "event_type" decodeVisitEventType
    |> required "reason" (Dec.maybe decodeVisitEventReason)
    |> required "method" decodeVisitEventMethod


decodeVisitEventType : Dec.Decoder VisitEventType
decodeVisitEventType =
  Dec.string |> Dec.andThen
    ( \str -> case str of
        "A" -> Dec.succeed VET_Arrival
        "P" -> Dec.succeed VET_Present
        "D" -> Dec.succeed VET_Departure
        other -> Dec.fail <| "Unknown visit event type: " ++ other
    )


decodeVisitEventMethod : Dec.Decoder VisitEventMethod
decodeVisitEventMethod =
  Dec.string |> Dec.andThen
    ( \str -> case str of
        "F" -> Dec.succeed VEM_FrontDesk
        "R" -> Dec.succeed VEM_Rfid
        "M" -> Dec.succeed VEM_MobileApp
        "U" -> Dec.succeed VEM_Unknown
        other -> Dec.fail <| "Unknown visit event type: " ++ other
    )

decodeVisitEventReason : Dec.Decoder VisitEventReason
decodeVisitEventReason =
  Dec.string |> Dec.andThen
    ( \str -> case str of
        "CLS" -> Dec.succeed VER_Class
        "CLB" -> Dec.succeed VER_Club
        "CUR" -> Dec.succeed VER_Curious
        "GST" -> Dec.succeed VER_Guest
        "MEM" -> Dec.succeed VER_Member
        "OTH" -> Dec.succeed VER_Other
        "PUB" -> Dec.succeed VER_PublicAccess
        "VOL" -> Dec.succeed VER_Volunteer
        other -> Dec.fail <| "Unknown visit event type: " ++ other
    )


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


-----------------------------------------------------------------------------
-- KMKR SHOWS
-----------------------------------------------------------------------------


type alias Show = Resource ShowData


type alias ShowData =
  { title : String
  , duration : Duration
  , description : String
  , active : Bool
  , hosts : List String
  , remainingSeconds : Float  -- Read-only, meaningful in "now playing" context, else 0.
  }


decodeShow : Dec.Decoder Show
decodeShow = decodeResource decodeShowData


decodeShowData : Dec.Decoder ShowData
decodeShowData =
  decode ShowData
    |> required "title" Dec.string
    |> required "duration" decodeDuration
    |> required "description" Dec.string
    |> required "active" Dec.bool
    |> optional "hosts" (Dec.list Dec.string) []
    |> optional "remaining_seconds" Dec.float 0.0


------------------


type alias Broadcast = Resource BroadcastData


type alias BroadcastData =
  { episode : ResourceUrl
  , date : CalendarDate
  , hostCheckedIn : Maybe ClockTime
  , theType : BroadcastType
  }


type BroadcastType
 = FirstBroadcast
 | RepeatBroadcast


decodeBroadcastData : Dec.Decoder BroadcastData
decodeBroadcastData =
  Dec.map4 BroadcastData
    (Dec.field "episode" decodeResourceUrl)
    (Dec.field "date" decodeCalendarDate)
    (Dec.field "host_checked_in" (Dec.maybe decodeClockTime))
    (Dec.field "type" broadcastTypeDecoder)


broadcastDataNVPs : BroadcastData -> List (String, Enc.Value)
broadcastDataNVPs bc =
  [ ( "episode", bc.episode |> Enc.string )
  , ( "date", bc.date |> encodeCalendarDate )
  , ( "host_checked_in", bc.hostCheckedIn |> EncX.maybe encodeClockTime )
  , ( "type", bc.theType |> encodeBroadcastType)
  ]


encodeBroadcastData : BroadcastData -> Enc.Value
encodeBroadcastData = Enc.object << broadcastDataNVPs


broadcastTypeDecoder : Dec.Decoder BroadcastType
broadcastTypeDecoder =
  Dec.string |> Dec.andThen
    ( \str ->
      case str of
        "1ST" -> Dec.succeed FirstBroadcast
        "RPT" -> Dec.succeed RepeatBroadcast
        other -> Dec.fail <| "Unknown broadcast type: " ++ other
    )


broadcastTypeToString : BroadcastType -> String
broadcastTypeToString x =
  case x of
    FirstBroadcast -> "1ST"
    RepeatBroadcast -> "RPT"


encodeBroadcastType : BroadcastType -> Enc.Value
encodeBroadcastType theType =
  broadcastTypeToString theType |> Enc.string


type BroadcastFilter
  = BroadcastsWithEpisodeIdEqualTo Int
  | BroadcastsWithTypeEqualTo BroadcastType


broadcastFilterToString : BroadcastFilter -> String
broadcastFilterToString filter =
  case filter of
    BroadcastsWithEpisodeIdEqualTo id -> "episode=" ++ toString id
    BroadcastsWithTypeEqualTo theType -> "type=" ++ broadcastTypeToString theType

------------------


type alias Episode = Resource EpisodeData


type alias EpisodeData =
  { show : ResourceUrl
  , firstBroadcast : CalendarDate
  , title : String
  , tracks : List EpisodeTrack
  }


type EpisodeFilter
  = EpisodeDateEquals CalendarDate
  | EpisodeShowEquals Int


episodeFilterToString : EpisodeFilter -> String
episodeFilterToString filter =
  case filter of
    EpisodeDateEquals d -> "first_broadcast=" ++ CalendarDate.toString d
    EpisodeShowEquals showNum -> "show=" ++ toString showNum


decodeEpisodeData : Dec.Decoder EpisodeData
decodeEpisodeData =
  Dec.map4 EpisodeData
    (Dec.field "show" decodeResourceUrl)
    (Dec.field "first_broadcast" decodeCalendarDate)
    (Dec.field "title" Dec.string)
    (Dec.field "tracks_embed" (Dec.list (decodeResource decodeEpisodeTrackData)))


episodeDataNVPs : EpisodeData -> List (String, Enc.Value)
episodeDataNVPs ep =
  [ ( "show", ep.show |> Enc.string )
  , ( "first_broadcast", ep.firstBroadcast |> encodeCalendarDate )
  , ( "title", ep.title |> Enc.string )
  ]


encodeEpisodeData : EpisodeData -> Enc.Value
encodeEpisodeData = Enc.object << episodeDataNVPs


------------------


type alias EpisodeTrack = Resource EpisodeTrackData


type alias EpisodeTrackData =
  { episode : ResourceUrl
  , sequence : Int
  , artist : String
  , title : String
  , duration : String
  , trackBroadcast : Maybe ResourceUrl
  }


decodeEpisodeTrackData : Dec.Decoder EpisodeTrackData
decodeEpisodeTrackData =
  Dec.map6 EpisodeTrackData
    (Dec.field "episode" decodeResourceUrl)
    (Dec.field "sequence" Dec.int)
    (Dec.field "artist" Dec.string)
    (Dec.field "title" Dec.string)
    (Dec.field "duration" Dec.string)
    (Dec.field "track_broadcast" (Dec.maybe <| decodeResourceUrl))


encodeEpisodeTrackData : EpisodeTrackData -> Enc.Value
encodeEpisodeTrackData etd = Enc.object
  [ ( "episode", etd.episode |> Enc.string )
  , ( "sequence", etd.sequence |> Enc.int )
  , ( "artist", etd.artist |> Enc.string)
  , ( "title", etd.title |> Enc.string)
  , ( "duration", etd.duration |> Enc.string )
  , ( "track_broadcast", etd.trackBroadcast |> (EncX.maybe Enc.string))
  ]


------------------

type alias TrackBroadcast = Resource TrackBroadcastData


type alias TrackBroadcastData =
  { start : PointInTime
  , libraryTrack : Maybe ResourceUrl
  , nonLibraryTrack : Maybe ResourceUrl
  , libraryTrackEmbed : Maybe Track
  , nonLibraryTrackEmbed : Maybe EpisodeTrack
  }


decodeTrackBroadcastData : Dec.Decoder TrackBroadcastData
decodeTrackBroadcastData =
  Dec.map5 TrackBroadcastData
    (Dec.field "start" decodePointInTime)
    (Dec.field "library_track" (Dec.maybe <| decodeResourceUrl))
    (Dec.field "non_library_track" (Dec.maybe <| decodeResourceUrl))
    (Dec.field "library_track_embed" (Dec.maybe <| decodeResource <| decodeTrackData))
    (Dec.field "non_library_track_embed" (Dec.maybe <| decodeResource <| decodeEpisodeTrackData))


encodeTrackBroadcastData : TrackBroadcastData -> Enc.Value
encodeTrackBroadcastData tbd = Enc.object
  [ ( "start", tbd.start |> encodePointInTime )
  , ( "library_track", tbd.libraryTrack |> (EncX.maybe Enc.string))
  , ( "non_library_track", tbd.nonLibraryTrack |> (EncX.maybe Enc.string))
  ]



-----------------------------------------------------------------------------
-- KMKR TRACKS
-----------------------------------------------------------------------------

type alias Track = Resource TrackData


type alias TrackData =
  { artist : String
  , durationSeconds : Float
  , radioDjId : Int
  , title : String
  , trackType : Int
  , remainingSeconds : Float  -- Read-only, meaningful in "now playing" context, else 0.
  }


decodeTrackData : Dec.Decoder TrackData
decodeTrackData =
  Dec.map6 TrackData
    (Dec.field "artist" Dec.string)
    (Dec.field "duration_seconds" Dec.float)
    (Dec.field "radiodj_id" Dec.int)
    (Dec.field "title" Dec.string)
    (Dec.field "track_type" Dec.int)
    (Dec.field "remaining_seconds" Dec.float)


-----------------------------------------------------------------------------
-- NON-REST FUNCTIONALITY
-----------------------------------------------------------------------------

-- LOGGING -------------------------------------------------------------

type LogLevel
  = LL_Debug
  | LL_Info
  | LL_Warning
  | LL_Error
  | LL_Critical

logLevelToStr : LogLevel -> String
logLevelToStr logLevel =
  case logLevel of
    LL_Debug -> "D"
    LL_Info -> "I"
    LL_Warning -> "W"
    LL_Error -> "E"
    LL_Critical -> "C"

type alias LogMessage msg = String -> LogLevel -> String -> (Result Http.Error String -> msg) -> Cmd msg
logMessage : XisRestFlags -> Authorization -> LogMessage msg
logMessage flags auth loggerName logLevel msgToLog tagger =
  let
    obj =
      [ ("logger_name", loggerName |> Enc.string)
      , ("log_level", logLevel |> logLevelToStr |> Enc.string)
      , ("msg_to_log", msgToLog |> Enc.string)
      ]
    val = Enc.object obj
    request = postRequestExpectingString
      auth
      flags.logMessageUrl
      val
  in
    Http.send tagger request


-- AUTHENTICATE -------------------------------------------------------------

type alias AuthenticationResult =
  { isAuthentic : Bool
  , authenticatedMember : Maybe Member
  }


authenticate: XisRestFlags -> Authorization
  -> String -> String -> (Result Http.Error AuthenticationResult -> msg)
  -> Cmd msg
authenticate flags auth userName password tagger =
  let
    request = postRequest
      auth
      flags.authenticateUrl
      decodeAuthenticationResult
      (encodeAuthenticateRequestData userName password)
  in
    Http.send tagger request


encodeAuthenticateRequestData : String -> String -> Enc.Value
encodeAuthenticateRequestData userName password =
  Enc.object
    [ ( "username", userName |> Enc.string )
    , ( "userpw", password |> Enc.string )
    ]


decodeAuthenticationResult : Dec.Decoder AuthenticationResult
decodeAuthenticationResult =
  decode AuthenticationResult
    |> required "is_authentic" Dec.bool
    |> optional "authenticated_member" (Dec.maybe (decodeResource decodeMemberData)) Nothing


-- SEND MEMBERSHIP INFO -----------------------------------------------------

type alias EmailMembershipInfo msg = Int -> (Result Http.Error String -> msg) -> Cmd msg
emailMembershipInfo : XisRestFlags -> Authorization -> EmailMembershipInfo msg
emailMembershipInfo flags auth memberId tagger =
  let
    val = Enc.object [("memberpk", Enc.int memberId)]
    request = postRequestExpectingString
      auth
      flags.emailMembershipInfoUrl
      val
  in
    Http.send tagger request

-- NOW PLAYING on KMKR -------------------------------------------------------------

type alias NowPlaying =
  { show : Maybe ShowData
  , track : Maybe TrackData
  }


decodeNowPlaying : Dec.Decoder NowPlaying
decodeNowPlaying =
  Dec.map2 NowPlaying
    (Dec.field "show" (Dec.maybe decodeShowData))
    (Dec.field "track" (Dec.maybe decodeTrackData))


nowPlaying: XisRestFlags -> Authorization -> (Result Http.Error NowPlaying -> msg) -> Cmd msg
nowPlaying flags auth tagger =
  let
    request = getRequest auth flags.nowPlayingUrl decodeNowPlaying
  in
    Http.send tagger request
