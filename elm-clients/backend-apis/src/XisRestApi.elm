module XisRestApi
  exposing
    ( createSession  -- Instantiate an API session
    , djangoizeId
    , setStatus  -- on Claim
    , setWitness  -- on Work
    , setWorkDuration  -- on Work
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
    , Task, TaskData
    , TaskListFilter (..)
    , TaskPriority (..)
    , TimeBlock, TimeBlockData
    , TimeBlockType, TimeBlockTypeData
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

staffingStatus_STAFFED = "S"  -- As defined in Django backend.

taskHighPriorityValue = "H"  -- As defined in Django backend.
taskMediumPriorityValue = "M"  -- As defined in Django backend.
taskLowPriorityValue = "L"  -- As defined in Django backend.


-----------------------------------------------------------------------------
-- GENERAL TYPES
-----------------------------------------------------------------------------

type alias XisRestFlags =
  ----- SECURITY -----
  { authorization : Authorization
  , csrfToken : String
  ----- ENDPOINTS -----
  , claimListUrl : ResourceListUrl
  , discoveryMethodsUrl : ResourceListUrl
  , memberListUrl : ResourceListUrl
  , membershipListUrl : ResourceListUrl
  , taskListUrl : ResourceListUrl
  , timeBlocksUrl : ResourceListUrl
  , timeBlockTypesUrl : ResourceListUrl
  , workListUrl : ResourceListUrl
  , workNoteListUrl : ResourceListUrl
  }


type alias ResultMessager rsrc msg = Result Http.Error rsrc -> msg

type alias GetterById rsrc msg =
  Int -> ResultMessager rsrc msg -> Cmd msg

type alias GetterFromUrl rsrc msg =
  ResourceUrl -> ResultMessager rsrc msg -> Cmd msg

type alias Replacer rsrc msg =
  rsrc -> ResultMessager rsrc msg -> Cmd msg

type alias Creator data rsrc msg =
  data -> ResultMessager rsrc msg -> Cmd msg

type alias Lister rsrc msg =
  ResultMessager (PageOf rsrc) msg -> Cmd msg

type alias FilteringLister filter rsrc msg =
  List filter -> ResultMessager (PageOf rsrc) msg -> Cmd msg


-----------------------------------------------------------------------------
-- API INSTANCE
-----------------------------------------------------------------------------

-- REVIEW: Instead of get, post, etc, how about Using DRF's "action" names?
-- They are: list, create, retrieve, update, partial_update, destroy.
-- How about: list, create, retrieve, replace, patch, destroy?

type alias Session msg =
  ----- SECURITY -----
  { authorization : Authorization
  , csrfToken : String
  ----- FUNCTIONALITY -----
  , claimUrl : Int -> ResourceUrl
  , coverTime : List Membership -> Time -> Bool
  , createClaim : Creator ClaimData Claim msg
  , createWork : Creator WorkData Work msg
  , createWorkNote : Creator WorkNoteData WorkNote msg
  , defaultBlockType : List TimeBlockType -> Maybe TimeBlockType
  , getBlocksTypes : TimeBlock -> List TimeBlockType -> List TimeBlockType
  , getMembershipById : GetterById Membership msg
  , getTaskById : GetterById Task msg
  , getTaskFromUrl : GetterFromUrl Task msg
  , listClaims : FilteringLister ClaimListFilter Claim msg
  , listDiscoveryMethods : Lister DiscoveryMethod msg
  , listMembers : FilteringLister MemberListFilter Member msg
  , listMemberships : FilteringLister MembershipListFilter Membership msg
  , listTasks : FilteringLister TaskListFilter Task msg
  , listTimeBlocks : Lister TimeBlock msg
  , listTimeBlockTypes : Lister TimeBlockType msg
  , listWorks : FilteringLister WorkListFilter Work msg
  , memberCanClaimTask : Int -> Task -> Bool
  , memberHasStatusOnTask : Int -> ClaimStatus -> Task -> Bool
  , membersClaimOnTask : Int -> Task -> Maybe Claim
  , membersStatusOnTask : Int -> Task -> Maybe ClaimStatus
  , memberUrl : Int -> ResourceUrl
  , mostRecentMembership : List Membership -> Maybe Membership
  , replaceClaim : Replacer Claim msg
  , replaceWork : Replacer Work msg
  , replaceWorkWithHeaders : List Http.Header -> Replacer Work msg
  , taskUrl : Int -> ResourceUrl
  , workUrl : Int -> ResourceUrl
  , workNoteUrl : Int -> ResourceUrl
  }

createSession : XisRestFlags -> Session msg
createSession flags =
  ----- SECURITY -----
  { authorization = flags.authorization
  , csrfToken = flags.csrfToken
  ----- FUNCTIONALITY -----
  , claimUrl = urlFromId flags.claimListUrl
  , coverTime = coverTime
  , createClaim = createClaim flags
  , createWork = createWork flags
  , createWorkNote = createWorkNote flags
  , defaultBlockType = defaultBlockType
  , getBlocksTypes = getBlocksTypes
  , getMembershipById = getMembershipById flags
  , getTaskById = getTaskById flags
  , getTaskFromUrl = getTaskFromUrl flags
  , listClaims = listClaims flags
  , listDiscoveryMethods = listDiscoveryMethods flags
  , listMembers = listMembers flags
  , listMemberships = listMemberships flags
  , listTasks = listTasks flags
  , listTimeBlocks = listTimeBlocks flags
  , listTimeBlockTypes = listTimeBlockTypes flags
  , listWorks = listWorks flags
  , memberCanClaimTask = memberCanClaimTask flags
  , memberHasStatusOnTask = memberHasStatusOnTask flags
  , membersClaimOnTask = membersClaimOnTask flags
  , membersStatusOnTask = membersStatusOnTask flags
  , memberUrl = urlFromId flags.memberListUrl
  , mostRecentMembership = mostRecentMembership
  , replaceClaim = replaceClaim flags
  , replaceWork = replaceWorkWithHeaders flags []
  , replaceWorkWithHeaders = replaceWorkWithHeaders flags
  , taskUrl = urlFromId flags.taskListUrl
  , workUrl = urlFromId flags.workListUrl
  , workNoteUrl = urlFromId flags.workNoteListUrl
  }


-----------------------------------------------------------------------------
-- TASKS
-----------------------------------------------------------------------------

type TaskPriority = HighPriority | MediumPriority | LowPriority


type alias TaskData =
  { claimSet : List Claim
  , creationDate : CalendarDate
  , deadline : Maybe CalendarDate
  , eligibleClaimants : List ResourceUrl
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

type alias Task = Resource TaskData

type TaskListFilter
  = ScheduledDateEquals CalendarDate
  -- | ScheduledDateInRange Date Date
  -- | WorkStartTimeRange ClockTime ClockTime


taskListFilterToString : TaskListFilter -> String
taskListFilterToString filter =
  case filter of
    ScheduledDateEquals d -> "scheduled_date=" ++ (CalendarDate.toString d)


listTasks : XisRestFlags -> FilteringLister TaskListFilter Task msg
listTasks flags filters resultToMsg =
  let
    request = httpGetRequest
      flags.authorization
      (filteredListUrl flags.taskListUrl filters taskListFilterToString)
      (decodePageOf decodeTask)
  in
    Http.send resultToMsg request


getTaskById : XisRestFlags -> GetterById Task msg
getTaskById flags taskNum resultToMsg =
  let url = urlFromId flags.taskListUrl taskNum
  in getTaskFromUrl flags url resultToMsg


getTaskFromUrl : XisRestFlags -> GetterFromUrl Task msg
getTaskFromUrl flags url resultToMsg =
  let
    request = httpGetRequest flags.authorization url decodeTask
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
    canClaim = memberIsEligible && (not task.data.isFullyClaimed)
    alreadyClaimed = memberHasStatusOnTask flags memberNum CurrentClaimStatus task
  in
    canClaim || alreadyClaimed


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

setStatus : ClaimStatus -> Claim ->  Claim
setStatus newSetting oldClaim =
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


listClaims : XisRestFlags -> FilteringLister ClaimListFilter Claim msg
listClaims flags filters resultToMsg =
  let
    request = httpGetRequest
      flags.authorization
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


replaceClaim : XisRestFlags -> Replacer Claim msg
replaceClaim flags claim resultToMsg =
  let
    request = Http.request
      { method = "PUT"
      , headers = [authenticationHeader flags.authorization]
      , url = urlFromId flags.claimListUrl claim.id
      , body = claim.data |> encodeClaimData |> Http.jsonBody
      , expect = Http.expectJson decodeClaim
      , timeout = Nothing
      , withCredentials = False
      }
  in
    Http.send resultToMsg request


createClaim : XisRestFlags -> Creator ClaimData Claim msg
createClaim flags claimData resultToMsg =
  let
    request = Http.request
      { method = "POST"
      , headers = [authenticationHeader flags.authorization]
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

setWitness : Maybe ResourceUrl -> Work ->  Work
setWitness newSetting oldWork =
  let
    data = oldWork.data
    newData = {data | witness = newSetting}
  in
    {oldWork | data = newData}


setWorkDuration : Maybe Duration -> Work -> Work
setWorkDuration newSetting oldWork =
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


listWorks : XisRestFlags -> FilteringLister WorkListFilter Work msg
listWorks flags filters resultToMsg =
  let
    request = httpGetRequest
      flags.authorization
      (filteredListUrl flags.workListUrl filters workListFilterToString)
      (decodePageOf decodeWork)
  in
    Http.send resultToMsg request


createWork : XisRestFlags -> Creator WorkData Work msg
createWork flags workData resultToMsg =
  let
    request = Http.request
      { method = "POST"
      , headers = [authenticationHeader flags.authorization]
      , url = flags.workListUrl
      , body = workData |> encodeWorkData |> Http.jsonBody
      , expect = Http.expectJson decodeWork
      , timeout = Nothing
      , withCredentials = False
      }
  in
    Http.send resultToMsg request


-- If "witness" is provided, the witness's password needs to be in an X-Witness-PW header.
replaceWorkWithHeaders : XisRestFlags -> List Http.Header -> Replacer Work msg
replaceWorkWithHeaders flags headers work resultToMsg =
  let
    request = Http.request
      { method = "PUT"
      , headers = headers ++ [authenticationHeader flags.authorization]
      , url = urlFromId flags.workListUrl work.id
      , body = work.data |> encodeWorkData |> Http.jsonBody
      , expect = Http.expectJson decodeWork
      , timeout = Nothing
      , withCredentials = False
      }
  in
    Http.send resultToMsg request


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


createWorkNote : XisRestFlags -> Creator WorkNoteData WorkNote msg
createWorkNote flags workNoteData resultToMsg =
  let
    request = Http.request
      { method = "POST"
      , headers = [authenticationHeader flags.authorization]
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
  , friendlyName : Maybe String  -- Read only
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


memberListFilterToString : MemberListFilter -> String
memberListFilterToString filter =
  case filter of
    RfidNumberEquals n -> "rfidnum=" ++ (toString n)
    UsernameEquals s -> "auth_user__username__iexact=" ++ s


listMembers : XisRestFlags -> FilteringLister MemberListFilter Member msg
listMembers flags filters resultToMsg =
  let
    request = httpGetRequest
      flags.authorization
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
    |> required "friendly_name" (Dec.maybe Dec.string)
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


listTimeBlockTypes : XisRestFlags -> Lister TimeBlockType msg
listTimeBlockTypes model resultToMsg =
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


listTimeBlocks : XisRestFlags -> Lister TimeBlock msg
listTimeBlocks flags resultToMsg =
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


listMemberships : XisRestFlags -> FilteringLister MembershipListFilter Membership msg
listMemberships flags filters resultToMsg =
  let
    request = httpGetRequest
      flags.authorization
      (filteredListUrl flags.membershipListUrl filters membershipListFilterToString)
      (decodePageOf decodeMembership)
  in
    Http.send resultToMsg request


getMembershipById : XisRestFlags -> GetterById Membership msg
getMembershipById flags memberNum resultToMsg =
  let url = urlFromId flags.memberListUrl memberNum
  in getMembershipFromUrl flags url resultToMsg


getMembershipFromUrl : XisRestFlags -> GetterFromUrl Membership msg
getMembershipFromUrl flags url resultToMsg =
  let
    request = httpGetRequest
      flags.authorization
      url
      decodeMembership
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


listDiscoveryMethods : XisRestFlags -> Lister DiscoveryMethod msg
listDiscoveryMethods flags resultToMsg =
  let request = Http.get flags.discoveryMethodsUrl (decodePageOf decodeDiscoveryMethod)
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