module XisRestApi
  exposing
    ( createSession  -- Instantiate an API session
    , djangoizeId
    , setClaimsDateVerified
    , setClaimsStatus
    , setWorksDuration
    , setWorksWitness
    --------------------
    , Claim, ClaimData
    , ClaimStatus (..)
    , ClaimListFilter (..)
    , DiscoveryMethod, DiscoveryMethodData
    , Member, MemberData
    , Membership, MembershipData
    , MemberListFilter (..)
    , MembershipListFilter (..)
    , Session
    , Task, StaffingStatus(..), TaskData
    , TaskListFilter (..)
    , TaskPriority (..)
    , TimeBlock, TimeBlockData
    , TimeBlockType, TimeBlockTypeData
    , VisitEvent, VisitEventData
    , VisitEventType(..), VisitEventReason(..), VisitEventListFilter(..), VisitEventMethod(..)
    , Work, WorkData
    , WorkNote, WorkNoteData
    , WorkListFilter (..)
    , XisRestFlags
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
import Date

-- Third party
import List.Extra as ListX

-- Local
import DjangoRestFramework as DRF exposing (..)
import ClockTime exposing (ClockTime)
import Duration exposing (Duration)
import CalendarDate exposing (CalendarDate)
import PointInTime exposing (PointInTime)
import RangeOfTime exposing (RangeOfTime)

-----------------------------------------------------------------------------
-- CONSTANTS
-----------------------------------------------------------------------------

-- As defined in Django backend:
staffingStatus_STAFFED     = "S"  -- There is a verified current claim.
staffingStatus_UNSTAFFED   = "U"  -- There is no current claim.
staffingStatus_PROVISIONAL = "P"  -- There is an unverified current claim.
staffingStatus_DONE        = "D"  -- A claim is marked as done.

-- As defined in Django backend:
taskHighPriorityValue   = "H"
taskMediumPriorityValue = "M"
taskLowPriorityValue    = "L"


-----------------------------------------------------------------------------
-- GENERAL TYPES
-----------------------------------------------------------------------------

type alias XisRestFlags =
  { claimListUrl : ResourceListUrl
  , discoveryMethodListUrl : ResourceListUrl
  , memberListUrl : ResourceListUrl
  , membershipListUrl : ResourceListUrl
  , taskListUrl : ResourceListUrl
  , timeBlocksUrl : ResourceListUrl  -- TODO: Should be timeBlockListUrl
  , timeBlockTypesUrl : ResourceListUrl  -- TODO: Should be timeBlockTypeListUrl
  , visitEventListUrl : ResourceListUrl
  , workListUrl : ResourceListUrl
  , workNoteListUrl : ResourceListUrl
  }


type alias Creator data rsrc msg =
  data -> ResultTagger rsrc msg -> Cmd msg

type alias DeleterByUrl msg =
  ResourceUrl -> StringTagger msg -> Cmd msg

type alias DeleterById msg =
  Int -> StringTagger msg -> Cmd msg

type alias FilteringLister filter rsrc msg =
  List filter -> ResultTagger (PageOf rsrc) msg -> Cmd msg

type alias GetterById rsrc msg =
  Int -> ResultTagger rsrc msg -> Cmd msg

type alias GetterFromUrl rsrc msg =
  ResourceUrl -> ResultTagger rsrc msg -> Cmd msg

type alias Lister rsrc msg =
  ResultTagger (PageOf rsrc) msg -> Cmd msg

type alias Replacer rsrc msg =
  rsrc -> ResultTagger rsrc msg -> Cmd msg

type alias ResultTagger rsrc msg =
  Result Http.Error rsrc -> msg

type alias StringTagger msg =
  Result Http.Error String -> msg


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
  , getTaskById : GetterById Task msg
  , getTaskFromUrl : GetterFromUrl Task msg
  , getWorkFromUrl : GetterFromUrl Work msg

  ----- RESOURCE CREATORS -----
  , createClaim : Creator ClaimData Claim msg
  , createWork : Creator WorkData Work msg
  , createWorkNote : Creator WorkNoteData WorkNote msg

  ----- RESOURCE DELETERS -----
  , deleteWorkById : DeleterById msg
  , deleteWorkByUrl : DeleterByUrl msg

  ----- RESOURCE LISTERS -----
  , listClaims : FilteringLister ClaimListFilter Claim msg
  , listDiscoveryMethods : Lister DiscoveryMethod msg
  , listMembers : FilteringLister MemberListFilter Member msg
  , listMemberships : FilteringLister MembershipListFilter Membership msg
  , listTasks : FilteringLister TaskListFilter Task msg
  , listTimeBlocks : Lister TimeBlock msg
  , listTimeBlockTypes : Lister TimeBlockType msg
  , listVisitEvents : FilteringLister VisitEventListFilter VisitEvent msg
  , listWorks : FilteringLister WorkListFilter Work msg

  ----- RESOURCE REPLACERS
  , replaceClaim : Replacer Claim msg
  , replaceWork : Replacer Work msg
  , replaceWorkWithHeaders : List Http.Header -> Replacer Work msg

  ----- RESOURCE URLS -----
  , claimUrl : Int -> ResourceUrl
  , memberUrl : Int -> ResourceUrl
  , taskUrl : Int -> ResourceUrl
  , workUrl : Int -> ResourceUrl
  , workNoteUrl : Int -> ResourceUrl

  ----- OTHER -----
  , coverTime : List Membership -> Time -> Bool
  , defaultBlockType : List TimeBlockType -> Maybe TimeBlockType
  , getBlocksTypes : TimeBlock -> List TimeBlockType -> List TimeBlockType
  , memberCanClaimTask : Int -> Task -> Bool
  , memberHasStatusOnTask : Int -> ClaimStatus -> Task -> Bool
  , membersClaimOnTask : Int -> Task -> Maybe Claim
  , membersStatusOnTask : Int -> Task -> Maybe ClaimStatus
  , membersWithStatusOnTask : ClaimStatus -> Task -> List ResourceUrl
  , mostRecentMembership : List Membership -> Maybe Membership
  }

createSession : XisRestFlags -> Authorization -> Session msg
createSession flags auth =

  ----- RESOURCE GETTERS -----
  { getMembershipById = getMembershipById flags auth
  , getTaskById = getTaskById flags auth
  , getTaskFromUrl = getTaskFromUrl flags auth
  , getWorkFromUrl = getWorkFromUrl flags auth

  ----- RESOURCE CREATORS -----
  , createClaim = createClaim flags auth
  , createWork = createWork flags auth
  , createWorkNote = createWorkNote flags auth

  ----- RESOURCE DELETERS -----
  , deleteWorkById = deleteWorkById flags auth
  , deleteWorkByUrl = deleteWorkByUrl flags auth

  ----- RESOURCE LISTERS -----
  , listClaims = listClaims flags auth
  , listDiscoveryMethods = listDiscoveryMethods flags auth
  , listMembers = listMembers flags auth
  , listMemberships = listMemberships flags auth
  , listTasks = listTasks flags auth
  , listTimeBlocks = listTimeBlocks flags auth
  , listTimeBlockTypes = listTimeBlockTypes flags auth
  , listVisitEvents = listVisitEvents flags auth
  , listWorks = listWorks flags auth

  ----- RESOURCE REPLACERS -----
  , replaceClaim = replaceClaim flags auth
  , replaceWork = replaceWorkWithHeaders flags auth []
  , replaceWorkWithHeaders = replaceWorkWithHeaders flags auth

  ----- RESOURCE URLS -----
  , claimUrl = urlFromId flags.claimListUrl
  , memberUrl = urlFromId flags.memberListUrl
  , taskUrl = urlFromId flags.taskListUrl
  , workUrl = urlFromId flags.workListUrl
  , workNoteUrl = urlFromId flags.workNoteListUrl

  ----- OTHER -----
  , coverTime = coverTime
  , defaultBlockType = defaultBlockType
  , getBlocksTypes = getBlocksTypes
  , memberCanClaimTask = memberCanClaimTask flags
  , memberHasStatusOnTask = memberHasStatusOnTask flags
  , membersClaimOnTask = membersClaimOnTask flags
  , membersStatusOnTask = membersStatusOnTask flags
  , membersWithStatusOnTask = membersWithStatusOnTask
  , mostRecentMembership = mostRecentMembership
  }


-----------------------------------------------------------------------------
-- TASKS
-----------------------------------------------------------------------------

type TaskPriority = HighPriority | MediumPriority | LowPriority

type StaffingStatus = SS_Staffed | SS_Unstaffed | SS_Provisional | SS_Done

type alias TaskData =
  { claimSet : List Claim
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

type alias Task = Resource TaskData

type TaskListFilter
  = ScheduledDateEquals CalendarDate
  -- | ScheduledDateInRange Date Date
  -- | WorkStartTimeRange ClockTime ClockTime


taskListFilterToString : TaskListFilter -> String
taskListFilterToString filter =
  case filter of
    ScheduledDateEquals d -> "scheduled_date=" ++ (CalendarDate.toString d)


listTasks : XisRestFlags -> Authorization -> FilteringLister TaskListFilter Task msg
listTasks flags auth filters resultToMsg =
  let
    request = httpGetRequest
      auth
      (filteredListUrl flags.taskListUrl filters taskListFilterToString)
      (decodePageOf decodeTask)
  in
    Http.send resultToMsg request


getTaskById : XisRestFlags -> Authorization -> GetterById Task msg
getTaskById flags auth taskNum resultToMsg =
  let url = urlFromId flags.taskListUrl taskNum
  in getTaskFromUrl flags auth url resultToMsg


getTaskFromUrl : XisRestFlags -> Authorization -> GetterFromUrl Task msg
getTaskFromUrl flags auth url resultToMsg =
  let
    request = httpGetRequest auth url decodeTask
  in
    Http.send resultToMsg request


--putTask : XisRestFlags -> Replacer Task msg
--putTask flags task resultToMsg =
--  let
--    request = Http.request
--      { method = "PUT"
--      , headers = [authenticationHeader flags.authorization]
--      , url = urlFromId flags.taskListUrl task.id
--      , body = task |> encodeTask |> Http.jsonBody
--      , expect = Http.expectJson decodeTask
--      , timeout = Nothing
--      , withCredentials = False
--      }
--  in
--    Http.send resultToMsg request


memberCanClaimTask : XisRestFlags -> Int -> Task -> Bool
memberCanClaimTask flags memberNum task =
  let
    url = urlFromId flags.memberListUrl memberNum
    memberIsEligible = List.member url task.data.eligibleClaimants
    canClaim = memberIsEligible && (task.data.isFullyClaimed |> not)
    alreadyClaimed = memberHasStatusOnTask flags memberNum CurrentClaimStatus task
    abandonedClaim = memberHasStatusOnTask flags memberNum AbandonedClaimStatus task
  in
    canClaim || alreadyClaimed || abandonedClaim

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


decodeTask : Dec.Decoder Task
decodeTask = decodeResource decodeTaskData


decodeTaskData : Dec.Decoder TaskData
decodeTaskData =
  decode TaskData
    |> required "claim_set" (Dec.list decodeClaim)
    |> required "creation_date" DRF.decodeCalendarDate
    |> required "deadline" (Dec.maybe DRF.decodeCalendarDate)
    |> required "eligible_claimants" (Dec.list decodeResourceUrl)
    |> required "instructions" Dec.string
    |> required "is_fully_claimed" Dec.bool
    |> required "max_work" DRF.decodeDuration
    |> required "max_workers" Dec.int
    |> required "name_of_likely_worker" (Dec.maybe Dec.string)
    |> required "owner" (Dec.maybe decodeResourceUrl)
    |> required "priority" taskPriorityDecoder
    |> required "reviewer" (Dec.maybe decodeResourceUrl)
    |> required "scheduled_date" DRF.decodeCalendarDate
    |> required "short_desc" Dec.string
    |> required "should_nag" Dec.bool
    |> required "staffing_status" staffingStatusDecoder
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

type alias ClaimData =
  { claimedDuration : Duration
  , claimedStartTime : Maybe ClockTime
  , claimedTask : ResourceUrl
  , claimingMember : ResourceUrl
  , dateVerified : Maybe CalendarDate
  , status : ClaimStatus
  , workSet : List ResourceUrl
  }


type alias Claim = Resource ClaimData


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


claimListFilterToString : ClaimListFilter -> String
claimListFilterToString filter =
  case filter of
    ClaimStatusEquals stat -> "status=" ++ (claimStatusValue stat)
    ClaimingMemberEquals membNum -> "claiming_member=" ++ (toString membNum)
    ClaimedTaskEquals taskNum -> "claimed_task=" ++ (toString taskNum)


listClaims : XisRestFlags -> Authorization -> FilteringLister ClaimListFilter Claim msg
listClaims flags auth filters resultToMsg =
  let
    request = httpGetRequest
      auth
      (filteredListUrl flags.claimListUrl filters claimListFilterToString)
      (decodePageOf decodeClaim)
  in
    Http.send resultToMsg request


decodeClaim : Dec.Decoder Claim
decodeClaim = decodeResource decodeClaimData


decodeClaimData : Dec.Decoder ClaimData
decodeClaimData =
  decode ClaimData
    |> required "claimed_duration" DRF.decodeDuration
    |> required "claimed_start_time" (Dec.maybe DRF.decodeClockTime)
    |> required "claimed_task" decodeResourceUrl
    |> required "claiming_member" decodeResourceUrl
    |> required "date_verified" (Dec.maybe DRF.decodeCalendarDate)
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
encodeClaim = encodeResource claimDataNVPs

encodeClaimData : ClaimData -> Enc.Value
encodeClaimData = Enc.object << claimDataNVPs

claimDataNVPs : ClaimData -> List (String, Enc.Value)
claimDataNVPs cd =
  [ ( "claiming_member", cd.claimingMember |> Enc.string )
  , ( "claimed_task", cd.claimedTask |> Enc.string )
  , ( "claimed_start_time", cd.claimedStartTime |> (EncX.maybe encodeClockTime))
  , ( "claimed_duration", cd.claimedDuration |> encodeDuration)
  , ( "status", cd.status |> encodeClaimStatus )
  , ( "date_verified", cd.dateVerified |> (EncX.maybe encodeCalendarDate))
  ]


replaceClaim : XisRestFlags -> Authorization -> Replacer Claim msg
replaceClaim flags auth claim resultToMsg =
  let
    request = Http.request
      { method = "PUT"
      , headers = [authenticationHeader auth]
      , url = urlFromId flags.claimListUrl claim.id
      , body = claim.data |> encodeClaimData |> Http.jsonBody
      , expect = Http.expectJson decodeClaim
      , timeout = Nothing
      , withCredentials = False
      }
  in
    Http.send resultToMsg request


createClaim : XisRestFlags -> Authorization -> Creator ClaimData Claim msg
createClaim flags auth claimData resultToMsg =
  let
    request = Http.request
      { method = "POST"
      , headers = [authenticationHeader auth]
      , url = flags.claimListUrl
      , body = claimData |> encodeClaimData |> Http.jsonBody
      , expect = Http.expectJson decodeClaim
      , timeout = Nothing
      , withCredentials = False
      }
  in
    Http.send resultToMsg request


-----------------------------------------------------------------------------
-- WORKS
-----------------------------------------------------------------------------

type alias WorkData =
  { claim: ResourceUrl
  , witness : Maybe ResourceUrl
  , workDate : CalendarDate
  , workDuration : Maybe Duration
  , workStartTime : Maybe ClockTime
  }


type alias Work = Resource WorkData


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


--{-| WorkPatch (used for partial updates) is the same as Work but all fields are optional -}
--type alias WorkPatch =
--  { claim: Maybe ResourceUrl
--  , witness : Maybe ResourceUrl
--  , workDate : Maybe CalendarDate
--  , workDuration : Maybe Duration
--  , workStartTime : Maybe ClockTime
--  }


type WorkListFilter
  = WorkedClaimEquals Int
  | WorkDurationIsNull Bool


workListFilterToString : WorkListFilter -> String
workListFilterToString filter =
  case filter of
    WorkedClaimEquals id -> "claim=" ++ (toString id)
    WorkDurationIsNull setting -> "work_duration__isnull=" ++ (setting |> toString |> String.toLower)


listWorks : XisRestFlags -> Authorization -> FilteringLister WorkListFilter Work msg
listWorks flags auth  filters resultToMsg =
  let
    request = httpGetRequest
      auth
      (filteredListUrl flags.workListUrl filters workListFilterToString)
      (decodePageOf decodeWork)
  in
    Http.send resultToMsg request

getWorkFromUrl : XisRestFlags -> Authorization -> GetterFromUrl Work msg
getWorkFromUrl flags auth url resultToMsg =
  let
    request = httpGetRequest auth url decodeWork
  in
    Http.send resultToMsg request

createWork : XisRestFlags -> Authorization -> Creator WorkData Work msg
createWork flags auth workData resultToMsg =
  let
    request = Http.request
      { method = "POST"
      , headers = [authenticationHeader auth]
      , url = flags.workListUrl
      , body = workData |> encodeWorkData |> Http.jsonBody
      , expect = Http.expectJson decodeWork
      , timeout = Nothing
      , withCredentials = False
      }
  in
    Http.send resultToMsg request


-- If "witness" is provided, the witness's password needs to be in an X-Witness-PW header.
replaceWorkWithHeaders : XisRestFlags -> Authorization -> List Http.Header -> Replacer Work msg
replaceWorkWithHeaders flags auth headers work resultToMsg =
  let
    request = Http.request
      { method = "PUT"
      , headers = headers ++ [authenticationHeader auth]
      , url = urlFromId flags.workListUrl work.id
      , body = work.data |> encodeWorkData |> Http.jsonBody
      , expect = Http.expectJson decodeWork
      , timeout = Nothing
      , withCredentials = False
      }
  in
    Http.send resultToMsg request


deleteWorkById : XisRestFlags -> Authorization -> DeleterById msg
deleteWorkById flags auth id tagger =
  let url = urlFromId flags.workListUrl id
  in deleteWorkByUrl flags auth url tagger


deleteWorkByUrl : XisRestFlags -> Authorization -> DeleterByUrl msg
deleteWorkByUrl flags auth url tagger =
  let request = httpDeleteRequest auth url
  in Http.send tagger request


encodeWork : Work -> Enc.Value
encodeWork = encodeResource workDataNVPs

encodeWorkData : WorkData -> Enc.Value
encodeWorkData = Enc.object << workDataNVPs

workDataNVPs : WorkData -> List (String, Enc.Value)
workDataNVPs wd =
  [ ( "claim", wd.claim |> Enc.string )
  , ( "witness", wd.witness |> (EncX.maybe Enc.string))
  , ( "work_date", wd.workDate |> DRF.encodeCalendarDate)
  , ( "work_duration", wd.workDuration |> (EncX.maybe DRF.encodeDuration))
  , ( "work_start_time", wd.workStartTime |> (EncX.maybe DRF.encodeClockTime))
  ]


decodeWork : Dec.Decoder Work
decodeWork = decodeResource decodeWorkData


decodeWorkData : Dec.Decoder WorkData
decodeWorkData =
  decode WorkData
    |> required "claim" decodeResourceUrl
    |> required "witness" (Dec.maybe DRF.decodeResourceUrl)
    |> required "work_date" DRF.decodeCalendarDate
    |> required "work_duration" (Dec.maybe DRF.decodeDuration)
    |> required "work_start_time" (Dec.maybe DRF.decodeClockTime)


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


createWorkNote : XisRestFlags -> Authorization -> Creator WorkNoteData WorkNote msg
createWorkNote flags auth workNoteData resultToMsg =
  let
    request = Http.request
      { method = "POST"
      , headers = [authenticationHeader auth]
      , url = flags.workNoteListUrl
      , body = workNoteData |> encodeWorkNoteData |> Http.jsonBody
      , expect = Http.expectJson decodeWorkNote
      , timeout = Nothing
      , withCredentials = False
      }
  in
    Http.send resultToMsg request


encodeWorkNote: WorkNote -> Enc.Value
encodeWorkNote = encodeResource workNoteDataNVPs

encodeWorkNoteData : WorkNoteData -> Enc.Value
encodeWorkNoteData = Enc.object << workNoteDataNVPs

{-| Name Value Pairs for WorkNoteData -}
workNoteDataNVPs : WorkNoteData -> List (String, Enc.Value)
workNoteDataNVPs wnd =
  [ ( "author", wnd.author |> (EncX.maybe Enc.string))
  , ( "content", wnd.content |> Enc.string)
  , ( "work", wnd.work |> Enc.string)
  , ( "when_written", wnd.whenWritten |> PointInTime.isoString |> Enc.string)
  ]


decodeWorkNote : Dec.Decoder WorkNote
decodeWorkNote = decodeResource decodeWorkNoteData


decodeWorkNoteData : Dec.Decoder WorkNoteData
decodeWorkNoteData =
  decode WorkNoteData
    |> required "author" (Dec.maybe DRF.decodeResourceUrl)
    |> required "content" Dec.string
    |> required "work" DRF.decodeResourceUrl
    |> required "when_written" (Dec.string |> Dec.andThen (PointInTime.fromString >> DecX.fromResult))


-----------------------------------------------------------------------------
-- MEMBER
-----------------------------------------------------------------------------

type alias MemberData =
  { email : Maybe String
  , firstName : Maybe String
  , friendlyName : String  -- Read only
  , isActive : Bool
  , isCurrentlyPaid : Bool  -- Read only
  , lastName : Maybe String
  , latestNonfutureMembership : Maybe Membership  -- Read only
  , userName : String
  }


type alias Member = Resource MemberData


type MemberListFilter
  = RfidNumberEquals Int
  | UsernameEquals String
  | UsernameContains String
  | UsernameStartsWith String
  | LastNameStartsWith String
  | LastNameEquals String


memberListFilterToString : MemberListFilter -> String
memberListFilterToString filter =
  case filter of
    RfidNumberEquals n -> "rfidnum=" ++ (toString n)
    UsernameEquals s -> "auth_user__username__iexact=" ++ s
    UsernameContains s -> "auth_user__username__icontains=" ++ s
    UsernameStartsWith s -> "auth_user__username__istartswith=" ++ s
    LastNameStartsWith s -> "auth_user__last_name__istartswith=" ++ s
    LastNameEquals s -> "auth_user__last_name__iexact=" ++ s


listMembers : XisRestFlags -> Authorization -> FilteringLister MemberListFilter Member msg
listMembers flags auth filters resultToMsg =
  let
    request = httpGetRequest
      auth
      (filteredListUrl flags.memberListUrl filters memberListFilterToString)
      (decodePageOf decodeMember)
  in
    Http.send resultToMsg request


decodeMember : Dec.Decoder Member
decodeMember = decodeResource decodeMemberData


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
    |> required "latest_nonfuture_membership" (Dec.maybe decodeMembership)
    |> required "username" Dec.string


-----------------------------------------------------------------------------
-- TIME BLOCK TYPES
-----------------------------------------------------------------------------

type alias TimeBlockTypeData =
  { name : String
  , description : String
  , isDefault : Bool
  }


type alias TimeBlockType = Resource TimeBlockTypeData


listTimeBlockTypes : XisRestFlags -> Authorization -> Lister TimeBlockType msg
listTimeBlockTypes model auth resultToMsg =
  let request = Http.get model.timeBlockTypesUrl (decodePageOf decodeTimeBlockType)
  in Http.send resultToMsg request


decodeTimeBlockType : Dec.Decoder TimeBlockType
decodeTimeBlockType = decodeResource decodeTimeBlockTypeData


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

type alias TimeBlockData =
  { isNow : Bool
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


type alias TimeBlock = Resource TimeBlockData


listTimeBlocks : XisRestFlags -> Authorization -> Lister TimeBlock msg
listTimeBlocks flags auth resultToMsg =
  let request = Http.get flags.timeBlocksUrl (decodePageOf decodeTimeBlock)
  in Http.send resultToMsg request


decodeTimeBlock : Dec.Decoder TimeBlock
decodeTimeBlock = decodeResource decodeTimeBlockData


decodeTimeBlockData : Dec.Decoder TimeBlockData
decodeTimeBlockData =
  decode TimeBlockData
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
    relatedBlockTypeIds = List.map idFromUrl specificBlock.data.types
    isRelatedBlockType x = List.member (Ok x.id) relatedBlockTypeIds
  in
    List.filter isRelatedBlockType allBlockTypes


-----------------------------------------------------------------------------
-- MEMBERSHIPS
-----------------------------------------------------------------------------

type alias MembershipData =
  { member : String
  , startDate : CalendarDate
  , endDate : CalendarDate
  , sale : Maybe Int  -- Memberships linked to group memberships don't have a sale.
  , sale_price : String
  , ctrlid : String
  , protected : Bool
  }


type alias Membership = Resource MembershipData


type MembershipListFilter
  = MembershipsWithMemberIdEqualTo Int


membershipListFilterToString : MembershipListFilter -> String
membershipListFilterToString filter =
  case filter of
    MembershipsWithMemberIdEqualTo id -> "member=" ++ (toString id)


listMemberships : XisRestFlags -> Authorization -> FilteringLister MembershipListFilter Membership msg
listMemberships flags auth filters resultToMsg =
  let
    request = httpGetRequest
      auth
      (filteredListUrl flags.membershipListUrl filters membershipListFilterToString)
      (decodePageOf decodeMembership)
  in
    Http.send resultToMsg request


getMembershipById : XisRestFlags -> Authorization -> GetterById Membership msg
getMembershipById flags auth memberNum resultToMsg =
  let url = urlFromId flags.memberListUrl memberNum
  in getMembershipFromUrl flags auth url resultToMsg


getMembershipFromUrl : XisRestFlags -> Authorization -> GetterFromUrl Membership msg
getMembershipFromUrl flags auth url resultToMsg =
  let
    request = httpGetRequest auth url decodeMembership
  in
    Http.send resultToMsg request


decodeMembership : Dec.Decoder Membership
decodeMembership = decodeResource decodeMembershipData


decodeMembershipData : Dec.Decoder MembershipData
decodeMembershipData =
  decode MembershipData
    |> required "member" Dec.string
    |> required "start_date" DRF.decodeCalendarDate
    |> required "end_date" DRF.decodeCalendarDate
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

type alias DiscoveryMethodData =
  { name : String
  , order : Int
  , visible : Bool
  }


type alias DiscoveryMethod = Resource DiscoveryMethodData


listDiscoveryMethods : XisRestFlags -> Authorization -> Lister DiscoveryMethod msg
listDiscoveryMethods flags auth resultToMsg =
  let request = Http.get flags.discoveryMethodListUrl (decodePageOf decodeDiscoveryMethod)
  in Http.send resultToMsg request


decodeDiscoveryMethod : Dec.Decoder DiscoveryMethod
decodeDiscoveryMethod = decodeResource decodeDiscoveryMethodData

decodeDiscoveryMethodData : Dec.Decoder DiscoveryMethodData
decodeDiscoveryMethodData =
  decode DiscoveryMethodData
    |> required "name" Dec.string
    |> required "order" Dec.int
    |> required "visible" Dec.bool



-----------------------------------------------------------------------------
-- VISIT EVENTS
-----------------------------------------------------------------------------

type alias VisitEventData =
  { who : Member
  , when : PointInTime
  , eventType : VisitEventType
  , reason: Maybe VisitEventReason
  , method: VisitEventMethod
  }


type alias VisitEvent = Resource VisitEventData

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
  | VER_Volunteer


type VisitEventType
  = VET_Arrival  -- REVIEW: Should try to make "reason" an argument of this constructor?
  | VET_Present
  | VET_Departure


eventTypeString : VisitEventType -> String
eventTypeString vet =
  case vet of
    VET_Arrival -> "A"
    VET_Departure -> "D"
    VET_Present -> "P"


eventMethodString : VisitEventMethod -> String
eventMethodString vet =
  case vet of
    VEM_Rfid -> "R"
    VEM_FrontDesk -> "F"
    VEM_MobileApp -> "M"
    VEM_Unknown -> "U"


type VisitEventListFilter
  = VEF_WhenGreaterOrEquals PointInTime
  | VEF_EventTypeEquals VisitEventType
  | VEF_EventMethodEquals VisitEventMethod


visitEventListFilterToString : VisitEventListFilter -> String
visitEventListFilterToString filter =
  case filter of
    VEF_WhenGreaterOrEquals pit -> "when__gte=" ++ (PointInTime.isoString pit)
    VEF_EventTypeEquals vet -> "event_type=" ++ eventTypeString(vet)
    VEF_EventMethodEquals meth -> "method=" ++ eventMethodString(meth)


listVisitEvents : XisRestFlags -> Authorization -> FilteringLister VisitEventListFilter VisitEvent msg
listVisitEvents flags auth filters resultToMsg =
  let
    request = httpGetRequest
      auth
      (filteredListUrl flags.visitEventListUrl filters visitEventListFilterToString)
      (decodePageOf decodeVisitEvent)
  in
    Http.send resultToMsg request


decodeVisitEvent : Dec.Decoder VisitEvent
decodeVisitEvent = decodeResource decodeVisitEventData


decodeVisitEventData : Dec.Decoder VisitEventData
decodeVisitEventData =
  decode VisitEventData
    |> required "who" decodeMember
    |> required "when" DRF.decodePointInTime
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
        "VOL" -> Dec.succeed VER_Volunteer
        other -> Dec.fail <| "Unknown visit event type: " ++ other
    )


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


djangoizeId : String -> String
djangoizeId rawId =
  -- Django allows alphanumeric, _, @, +, . and -.
  replaceAll {oldSub="[^-a-zA-Z0-9_@+.]", newSub="_"} rawId


replaceAll : {oldSub : String, newSub : String} -> String -> String
replaceAll {oldSub, newSub} whole =
  Regex.replace Regex.All (regex oldSub) (\_ -> newSub) whole