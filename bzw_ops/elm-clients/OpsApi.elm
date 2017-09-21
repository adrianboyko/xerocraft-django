module OpsApi exposing
  ( getTimeBlocks
  , getTimeBlockTypes
  , TimeBlock
  , TimeBlockType
  , PageOfTimeBlocks
  , PageOfTimeBlockTypes
  )

-- Standard
import Json.Decode as Dec
import Json.Encode as Enc
import Regex exposing (regex)
import Http

-- Third-Party
import Json.Decode.Pipeline exposing (decode, required, optional, hardcoded)

-- Local

-----------------------------------------------------------------------------
-- UTILITIES
-----------------------------------------------------------------------------

replaceAll : String -> String -> String -> String
replaceAll oldSub newSub theString =
  Regex.replace Regex.All (regex oldSub) (\_ -> newSub) theString

-----------------------------------------------------------------------------
-- API TYPES
-----------------------------------------------------------------------------

type alias OpsApiModel a =
  { a
  | timeBlocksUrl : String
  , timeBlockTypesUrl : String
  }

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

type alias TimeBlockType =
  { id : Int
  , name : String
  , description : String
  }

-- Following is the response format of Django Rest Framework
type alias PageOf a =
  { count : Int
  , next : Maybe String
  , previous: Maybe String
  , results: List a
  }

type alias PageOfTimeBlocks = PageOf TimeBlock

type alias PageOfTimeBlockTypes = PageOf TimeBlockType


-----------------------------------------------------------------------------
-- API
-----------------------------------------------------------------------------

getTimeBlocks : OpsApiModel a -> (Result Http.Error PageOfTimeBlocks -> msg) -> Cmd msg
getTimeBlocks model resultToMsg =
  let request = Http.get model.timeBlocksUrl (decodePageOf decodeTimeBlock)
  in Http.send resultToMsg request

getTimeBlockTypes : OpsApiModel a -> (Result Http.Error PageOfTimeBlockTypes -> msg) -> Cmd msg
getTimeBlockTypes model resultToMsg =
  let request = Http.get model.timeBlockTypesUrl (decodePageOf decodeTimeBlockType)
  in Http.send resultToMsg request


-----------------------------------------------------------------------------
-- JSON
-----------------------------------------------------------------------------

decodeTimeBlockType : Dec.Decoder TimeBlockType
decodeTimeBlockType =
  Dec.map3 TimeBlockType
    (Dec.field "id" Dec.int)
    (Dec.field "name" Dec.string)
    (Dec.field "description" Dec.string)

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

decodePageOf : Dec.Decoder a -> Dec.Decoder (PageOf a)
decodePageOf decoder =
  decode PageOf
    |> required "count" Dec.int
    |> required "next" (Dec.maybe Dec.string)
    |> required "previous" (Dec.maybe Dec.string)
    |> required "results" (Dec.list decoder)

