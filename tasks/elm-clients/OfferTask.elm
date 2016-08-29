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
  , calendar_url: String
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
  | DeclineTask
  | OKItIsClaimed
  | CreateClaimSuccess String
  | CreateClaimFailure Http.Error

update : Msg -> Model -> (Model, Cmd Msg)
update action model =
  case action of

    ClaimTask ->
      (model, createClaim model.params.task_id)

    CreateClaimSuccess msg ->
      (model, Cmd.none)

    CreateClaimFailure err ->
      (model, Cmd.none)

    DeclineTask ->
      (model, Cmd.none)

    OKItIsClaimed ->
      ({model | step = Thanks}, Cmd.none)

createClaim : Int -> Cmd Msg
createClaim taskId =
  let
    url = "https://localhost:8000/tasks/api/claim/"
  in
    Cmd.none

-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

unselectable = style
  [ ("-moz-user-select", "-moz-none")
  , ("-khtml-user-select", "none")
  , ("-webkit-user-select", "none")
  , ("-ms-user-select", "none")
  , ("user-select", "none")
  ]

containerStyle = style
  [ ("text-align", "center")
  , ("padding", "10% 0")
  , ("font-family", "Roboto Condensed, Arial, Helvetica, sans-serif")
  ]

taskCardStyle = style
  [ ("display", "inline-block")
  , ("padding", "12px 12px") -- vert, horiz
  , ("margin", "17px")
  , ("background-color", "#ffe4b2")
  , ("color", "black")
  , ("border-radius", "8px")
  , ("border-style", "solid")
  , ("border-color", "black")
  , ("border-width", "1px")
  ]

buttonStyle = style
  [ ("font-size", "1.2em")
  , ("margin", "12px 7px") -- vert, horiz
  , ("padding", "7px 13px")
  ]

greetingStyle = style
  [ ("font-size", "2.5em")
  , ("font-weight", "bold")
  , ("margin", "0 0 0 0")
  ]

taskDescStyle = style
  [ ("font-size", "1.25em")
  , ("font-weight", "bold")
  ]

isClaimedStyle = style
    [ ("display", "inline-block")
    , ("background", "white")
    , ("color", "black")
    , ("margin", "0px")
    ]

-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : Model -> Html Msg
view {step, params} =
  case step of
    OfferTask -> offerTaskView params
    MoreTasks -> moreTasksView params
    Thanks -> thanksView params

offerTaskView : Params -> Html Msg
offerTaskView params =
  div [containerStyle, unselectable]
    [ div [greetingStyle] [text ("Hi " ++ params.user_friendly_name++"!")]
    , div [] [text "You have clicked the following task:"]
    , div [taskCardStyle]
        [ div [taskDescStyle] [text params.task_desc]
        , div [] [text params.task_day_str]
        , div [] [text params.task_time_str]
        ]
    , if (String.isEmpty params.already_claimed_by) then
        div []
          [ div [] [ text "Nobody is helping with this task." ]
          , div [] [ text "Will you staff it?" ]
          , button [buttonStyle, onClick ClaimTask] [text "Yes"]
          , button [buttonStyle, onClick DeclineTask] [text "No"]
          ]
      else
        div []
          [ div [isClaimedStyle]
            [ text ("Thanks for your interest, but " ++ params.already_claimed_by)
            , br [] []
            , text "has already claimed this task."
            ]
          , div [] [button [buttonStyle, onClick OKItIsClaimed] [text "OK"]]
          ]
    ]

moreTasksView : Params -> Html Msg
moreTasksView params =
  div [containerStyle] [text "hi"]

thanksView : Params -> Html Msg
thanksView params =
  div [containerStyle, unselectable]
    [ div [greetingStyle] [text "All Done"]
    , br [] []
    , div []
      [ text "If you haven't already done so, consider", br [] []
      , text "subscribing to your Xerocraft calendar so", br [] []
      , text "that your phone or computer can remind you", br [] []
      , text "of upcoming tasks. A link to your calendar", br [] []
      , text "(in 'icalendar' format) appears below:"
      ]
    , br [] []
    , a [ href params.calendar_url ] [ text (params.user_friendly_name ++ "'s Calendar") ]
    ]

-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------

subscriptions : Model -> Sub Msg
subscriptions model =
  Sub.none
