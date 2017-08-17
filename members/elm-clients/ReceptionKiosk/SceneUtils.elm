
module ReceptionKiosk.SceneUtils exposing (..)

-- Standard
import Html exposing (Html, div, img, text, p, span)
import Html.Attributes exposing (style, src, id, tabindex, width, height)
import Task

-- Third Party
import Material.Textfield as Textfield
import Material.Button as Button
import Material.Toggles as Toggles
import Material.Chip as Chip
import Material.Options as Options exposing (css)
import Material.List as Lists
import Material as Mat
import List.Nonempty exposing (Nonempty)

-- Local
import ReceptionKiosk.Types exposing (..)


send : msg -> Cmd msg
send msg =
  Task.succeed msg
  |> Task.perform identity

type alias SceneUtilModel a = {a|mdl : Mat.Model, flags : Flags, sceneStack : Nonempty Scene}

-----------------------------------------------------------------------------
-- VIEW UTILITIES
-----------------------------------------------------------------------------

sceneFrame : (SceneUtilModel a) -> List (Html Msg) -> Html Msg
sceneFrame model sceneHtml =
  div [frameDivStyle]
    [ img [src model.flags.bannerTopUrl, bannerTopStyle] []
    , div [sceneDivStyle] sceneHtml
    , frameNavButtons model
    , img [src model.flags.bannerBottomUrl, bannerBottomStyle] []
    ]

frameNavButtons : (SceneUtilModel a) -> Html Msg
frameNavButtons model =
  div [navDivStyle]
    (
    if not (List.Nonempty.isSingleton model.sceneStack)
    then
      [ Button.render MdlVector [10000] model.mdl
          ([Button.flat, Options.onClick Pop]++navButtonCss)
          [text "Back"]
      , hspace 600
      , Button.render MdlVector [10001] model.mdl
          ([Button.flat, Options.onClick (Push Welcome)]++navButtonCss)
          [text "Quit"]
      ]
    else
      [text ""]
    )

genericScene : (SceneUtilModel a) -> String -> String -> Html Msg -> List (ButtonSpec Msg) -> Html Msg
genericScene model title subtitle extraContent buttonSpecs =
  let sceneHtml =
    [ p [sceneTitleStyle] [text title]
    , p [sceneSubtitleStyle] [text subtitle]
    , extraContent
    , vspace 50
    -- TODO: Print BAD NEWS here.
    , div [] (List.map (sceneButton model) buttonSpecs)
    ]
  in sceneFrame model sceneHtml

type alias ButtonSpec msg = { title : String, msg: msg }
sceneButton : (SceneUtilModel a) -> ButtonSpec Msg -> Html Msg
sceneButton model buttonSpec =
  Button.render MdlVector [0] model.mdl
    ([ Button.raised, Options.onClick buttonSpec.msg]++sceneButtonCss)
    [ text buttonSpec.title ]

sceneGenericTextField : (SceneUtilModel a) -> Int -> String -> String -> (String -> Msg) -> List (Textfield.Property Msg) -> Html Msg
sceneGenericTextField model index hint value msger options =
  Textfield.render MdlVector [index] model.mdl
    ( [ Textfield.label hint
      , Textfield.floatingLabel
      , Textfield.value value
      , Options.onInput msger
      , css "width" "500px"
      ] ++ options
    )
    (text "spam") -- What is this Html Msg argument?

sceneTextField : (SceneUtilModel a) -> Int -> String -> String -> (String -> Msg) -> Html Msg
sceneTextField model index hint value msger =
  sceneGenericTextField model index hint value msger []

scenePasswordField : (SceneUtilModel a) -> Int -> String -> String -> (String -> Msg) -> Html Msg
scenePasswordField model index hint value msger =
  sceneGenericTextField model index hint value msger [Textfield.password]

sceneEmailField : (SceneUtilModel a) -> Int -> String -> String -> (String -> Msg) -> Html Msg
sceneEmailField model index hint value msger =
  sceneGenericTextField model index hint value msger [Textfield.email]

sceneCheckbox : (SceneUtilModel a) -> Int -> String -> Bool -> Msg -> Html Msg
sceneCheckbox model index label value msger =
  -- Toggle.checkbox doesn't seem to handle centering very well. The following div compensates for that.
  div [style ["text-align"=>"left", "display"=>"inline-block", "width"=>"400px"]]
    [ Toggles.checkbox MdlVector [index] model.mdl
        [ Options.onToggle msger
        , Toggles.value value
        ]
        [span [style ["font-size"=>"24pt", "margin-left"=>"16px"]] [ text label ]]
    ]

formatBadNews: List String -> Html Msg
formatBadNews msgs =
  if msgs == [] then text ""
  else
      div []
        (List.concat
          [ [ span [style ["font-size"=>"32pt"]] [text "Whoops!"], vspace 15 ]
          , List.map
              (\msg -> p [errorMsgStyle] [text msg])
              msgs
          , [ span [] [text "Please correct these issues and try again."] ]
          ]
        )

vspace : Int -> Html Msg
vspace amount =
  div [style ["height" => (toString amount ++ "px")]] []

hspace : Int -> Html Msg
hspace amount =
  div [style ["display" => "inline-block", "width" => (toString amount ++ "px")]] []


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

(=>) = (,)

px : Int -> String
px num = (toString num) ++ "px"

sceneWidth = 800
sceneHeight = 1280
topBannerHeight = 155
bottomBannerHeight = 84

frameDivStyle = style
  [ "font-family" => "Roboto Condensed, Arial, Helvetica"
  , "text-align" => "center"
  , "padding-left" => "0"
  , "padding-right" => "0"
  , "padding-top" => px topBannerHeight
  , "padding-bottom" => px bottomBannerHeight
  , "position" => "absolute"
  , "top" => "0"
  , "bottom" => "0"
  , "left" => "0"
  , "right" => "0"
  ]

sceneDivBorderWidth = 1
sceneDivStyle = style
  [ "margin-left" => "auto"
  , "margin-right" => "auto"
  , "border" => "1px solid #bbbbbb"
  , "background-color" => "white"
  , "width" => px (sceneWidth - 2*sceneDivBorderWidth)
  , "min-height" => "99.8%"
  ]

sceneTitleStyle = style
  [ "font-size" => "32pt"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "margin-top" => "2em"
  , "margin-bottom" => "0.5em"
  ]

sceneSubtitleStyle = style
  [ "font-size" => "24pt"
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "margin-bottom" => "1em"
  , "margin-top" => "0"
  ]

bannerTopStyle = style
  [ "display" => "block"
  , "margin-top" => px (-1*topBannerHeight)
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "height" => px topBannerHeight
  , "width" => px sceneWidth
  ]

bannerBottomStyle = style
  [ "display" => "block"
  , "margin-bottom" => px (-1*bottomBannerHeight)
  , "margin-left" => "auto"
  , "margin-right" => "auto"
  , "height" => px bottomBannerHeight
  , "width" => px sceneWidth
  ]

navDivStyle = bannerBottomStyle

errorMsgStyle = style
  [ "color"=>"red"
  , "font-size"=>"22pt"
  ]

navButtonCss =
  [ css "display" "inline-block"
  , css "margin-top" "30px"
  , css "font-size" "14pt"
  , css "color" "#eeeeee"
  ]

sceneButtonCss =
  [ css "margin-left" "10px"
  , css "margin-right" "10px"
  , css "padding-top" "25px"
  , css "padding-bottom" "55px"
  , css "padding-left" "30px"
  , css "padding-right" "30px"
  , css "font-size" "18pt"
  ]
