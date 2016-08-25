module OfferTask exposing (..)

import Html exposing (..)
import Html.App as Html
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as Json
import Task
import String

main =
  Html.programWithFlags
    { init = init
    , view = view
    , update = update
    , subscriptions = subscriptions
    }

-----------------------------------------------------------------------------
-- MODEL
-----------------------------------------------------------------------------

type Step
  = OfferTask  -- Offer the task the user clicked on
  | MoreTasks  -- Offer future instances of the task
  | Thanks     -- Thank the user and remind them of calendar

-- These are the parameters pushed into Elm's main when JS starts Elm.
-- They can't include the Step because Elm doesn't allow Union types to be pushed to main.
-- Many of these could be fetched via API, but might as well push them with the first request.
type alias Params =
  { auth_token : String
  , nag_id : Int
  , task_id : Int
  , user_friendly_name : String
  , task_desc : String
  , task_day_str : String
  , task_time_str: String
  , already_claimed_by: String
  , future_dates: List String
  , calendar_token: String
}

type alias Model =
  { step: Step
  , params: Params
  }

init : Maybe Params -> (Model, Cmd Msg)
init providedParams =
    case providedParams of
      Just pp -> ({step = OfferTask, params = pp}, Cmd.none)
      Nothing -> Debug.crash "Parameters MUST be provided by Javascript."

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

type Msg
  = ClaimTask
  | Unsubscribe

update : Msg -> Model -> (Model, Cmd Msg)
update action model =
  case action of
    ClaimTask ->
      (model, Cmd.none)
    Unsubscribe ->
      (model, Cmd.none)

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

containerStyle = style
  [ ("text-align", "center")
  , ("padding", "10% 0")
  , ("font-family", "Arial, Helvetica, sans-serif")
  ]

taskCardStyle = style
  [ ("display", "inline-block")
  , ("padding", "7pt 50pt 7pt")
  , ("margin", "10pt")
  , ("background-color", "#ffe4b2")
  , ("color", "black")
  , ("border-radius", "6pt")
  , ("border-style", "solid")
  , ("border-color", "black")
  , ("border-width", "1px")
  ]

buttonStyle = style
  [ ("font-size", "12pt")
  , ("margin", "9pt 0 0 0")
  , ("padding", "5pt 15pt")
  ]

view : Model -> Html Msg
view {step, params} =
  case step of
    OfferTask -> offerTaskView params
    MoreTasks -> moreTasksView params
    Thanks -> thanksView params

offerTaskView : Params -> Html Msg
offerTaskView params =
  let
    greetingStyle = style [("font-size", "24pt"), ("font-weight", "bold"), ("margin", "0 0 0pt 0")] -- TRBL
    taskDescStyle = style [("font-size", "16pt"), ("font-weight", "bold")]
    isClaimedStyle = style
        [ ("display", "inline-block")
        , ("background", "white")
        , ("color", "black")
        , ("margin", "0px") -- TRBL
        ]
  in
  div [containerStyle]
    [ div [greetingStyle] [text ("Hi " ++ params.user_friendly_name++"!")]
    , div [] [text "You have clicked the following task:"]
    , div [taskCardStyle]
        [ div [taskDescStyle] [text params.task_desc]
        , div [] [text params.task_day_str]
        , div [] [text params.task_time_str]
        ]
    , if (String.isEmpty params.already_claimed_by) then
        div []
          [ div [] [ text "Nobody is helping with this task. You can:" ]
          , div [] [ button [buttonStyle, onClick ClaimTask] [text "Claim Task!"] ]
          ]
      else
        div []
          [ div [isClaimedStyle]
            [ text ("Thanks for your interest, but " ++ params.already_claimed_by)
            , br [] []
            , text "has already claimed this task."
            ]
          , div [] [button [buttonStyle, onClick Unsubscribe] [text "OK"]]
          ]
    ]

moreTasksView : Params -> Html Msg
moreTasksView params =
  div [containerStyle] [text "hi"]

thanksView : Params -> Html Msg
thanksView params =
  div [containerStyle] [text "hi"]

-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------

subscriptions : Model -> Sub Msg
subscriptions model =
  Sub.none
