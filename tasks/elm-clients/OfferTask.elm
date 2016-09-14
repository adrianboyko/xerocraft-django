module OfferTask exposing (..)

import Html exposing (..)
import Html.App as Html
import Html.Attributes exposing (..)
import Html.Events exposing (..)
import Http
import Json.Decode as Dec
import Json.Encode as Enc
import Task
import String

-----------------------------------------------------------------------------
-- UTILITIES
-----------------------------------------------------------------------------

toStr v =
  let
    str = toString v
  in
    if String.left 1 str == "\"" then
      String.dropRight 1 (String.dropLeft 1 str)
    else
      str

-----------------------------------------------------------------------------
-- MAIN
-----------------------------------------------------------------------------

main =
  Html.programWithFlags
    { init = init
    , view = view
    , update = update
    , subscriptions = (\_ -> Sub.none)
    }

-----------------------------------------------------------------------------
-- MODEL
-----------------------------------------------------------------------------

type Scene
  = OfferTask  -- Offer the task the user clicked on
  | MoreTasks  -- Offer future instances of the task
  | Thanks     -- Thank the user and remind them of calendar

-- These are the parameters pushed into Elm's main when JS starts Elm.
-- They can't include the Scene because Elm doesn't allow Union types to be pushed to main.
-- Many of these could be fetched via API, but might as well push them with the first request.
type alias Params =
  { auth_token : String
  , task_id : Int
  , user_friendly_name : String
  , nagged_member_id : Int
  , task_desc : String
  , task_day_str : String
  , task_window_str: String
  , task_work_start_str: String
  , task_work_dur_str: String
  , already_claimed_by: String
  , future_task_ids: List Int
  , calendar_url: String
  , today_str: String
  , claim_list_uri: String
  , task_list_uri: String
  , member_list_uri: String

}

type alias Model =
  { scene: Scene
  , params: Params
  , probPt1: String
  , probPt2: String
  }

init : Maybe Params -> (Model, Cmd Msg)
init providedParams =
  case providedParams of
    Just pp -> ({scene = OfferTask, params = pp, probPt1 = "", probPt2 = ""}, Cmd.none)
    Nothing -> Debug.crash "Parameters MUST be provided by Javascript."

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

type Msg
  = ClaimTask
  | DeclineTask
  | ThankUser
  | CreateClaimSuccess Http.Response
  | CreateClaimFailure Http.RawError

update : Msg -> Model -> (Model, Cmd Msg)
update action model =
  case action of

    ClaimTask ->
      let p = model.params
      in
        (model, createClaim
          p.task_id
          p.nagged_member_id
          p.auth_token
          p.task_work_start_str
          p.task_work_dur_str
          p.today_str)

    CreateClaimSuccess response ->
      if response.status == 201 then
        -- The claim was successfully created so go to next scene.
        ({model|scene = MoreTasks, probPt1 = "", probPt2 = ""}, Cmd.none)
      else
        -- It's possible for the request to succeed but for creation to fail.
        case response.value of
          Http.Text someText ->
            ({model|probPt1 = response.statusText, probPt2 = someText}, Cmd.none)
          Http.Blob aBlob ->
            ({model|probPt1 = response.statusText, probPt2 = "<blob>"}, Cmd.none)

    CreateClaimFailure err ->
      case err of
        Http.RawTimeout ->
          (model, Cmd.none)
        Http.RawNetworkError ->
          (model, Cmd.none)

    DeclineTask ->
      (model, Cmd.none)

    ThankUser ->
      ({model | scene = Thanks}, Cmd.none)


createClaim : Int -> Int -> String -> String -> String-> String -> Cmd Msg
createClaim taskId memberId authToken claimedStartTime claimedDuration today =
  let
    -- TODO: These should be passed in from Django, not hard-coded here.
    claimUrl = "http://localhost:8000/tasks/api/claims/"
    memberUrl = "http://localhost:8000/members/api/members/"
    taskUrl = "http://localhost:8000/tasks/api/tasks/"

    newClaimBody =
      [ ("claiming_member", Enc.string (memberUrl++(toString memberId)++"/"))
      , ("claimed_task", Enc.string (taskUrl++(toString taskId)++"/"))
      , ("claimed_start_time", Enc.string claimedStartTime)
      , ("claimed_duration", Enc.string claimedDuration)
      , ("status", Enc.string "C") -- Current
      , ("date_verified", Enc.string today)
      ]
        |> Enc.object
        |> Enc.encode 0
        |> Http.string

  in
    Task.perform
      CreateClaimFailure
      CreateClaimSuccess
      (
        Http.send
          Http.defaultSettings
          { verb = "POST"
          , headers =
            [ ("Authentication", "Bearer " ++ authToken)
            , ("Content-Type", "application/json")
            ]
          , url = claimUrl
          , body = newClaimBody
          }
      )


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
view {scene, params, probPt1, probPt2} =
  case scene of
    OfferTask -> offerTaskView params probPt1 probPt2
    MoreTasks -> moreTasksView params
    Thanks -> thanksView params

offerTaskView : Params -> String -> String -> Html Msg
offerTaskView params probPt1 probPt2 =
  div [containerStyle, unselectable]
    [ div [greetingStyle] [text ("Hi " ++ params.user_friendly_name++"!")]
    , div [] [text "You have clicked the following task:"]
    , div [taskCardStyle]
        [ div [taskDescStyle] [text params.task_desc]
        , div [] [text params.task_day_str]
        , div [] [text params.task_window_str]
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
          , div [] [button [buttonStyle, onClick ThankUser] [text "OK"]]
          ]
    , div [] [text probPt1, br [] [], text probPt2]
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
