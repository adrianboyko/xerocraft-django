port module Wizard.SceneUtils exposing
  ( ButtonSpec
  , PadButtonSpec
  -------------------
  , blankGenericScene
  , currentScene
  , focusOnIndex
  , genericScene
  , hideKeyboard
  , hspace
  , msgForReset
  , msgForSegueTo
  , option_NoTabIndex
  , rebase
  , rebaseTo
  , padButton
  , px
  , pop
  , popTo
  , pt
  , replaceWith
  , sceneHeight
  , sceneWidth
  , sceneButton
  , sceneEmailField
  , sceneIsVisible
  , scenePasswordField
  , sceneTextArea
  , sceneTextBlockStyle
  , sceneTextField
  , sceneTextStyle
  , segueTo
  , send
  , textAreaColor
  , userIdStyle
  , vspace
  , (=>)
  )

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
import Material as Material
import List.Nonempty exposing (Nonempty)

-- Local
import Types exposing (..)


-----------------------------------------------------------------------------
-- PORTS
-----------------------------------------------------------------------------

{-| This will hide the keyboard using the Kiosk App's API.
-}
port hideKeyboard : () -> Cmd msg  -- Note that () might go away, per https://github.com/evancz/guide.elm-lang.org/issues/34


-----------------------------------------------------------------------------
-- MISC
-----------------------------------------------------------------------------

type alias KioskModel a =
  { a
  | mdl : Material.Model
  , flags : Flags
  , sceneStack : Nonempty Scene
  }

-----------------------------------------------------------------------------
-- MISC
-----------------------------------------------------------------------------

type alias Index = List Int  -- elm-mdl doesn't expose this type.

send : msg -> Cmd msg
send msg =
  Task.succeed msg
  |> Task.perform identity


-- REVIEW: Rename segueTo to push, to match pop?
segueTo : Scene -> Cmd Msg
segueTo scene = send (msgForSegueTo scene)

msgForSegueTo : Scene -> Msg
msgForSegueTo = WizardVector << Push

focusOnIndex : List Int -> Cmd Msg
focusOnIndex idx =
  send <| WizardVector <| FocusOnIndex idx

pop : Cmd Msg
pop = send (WizardVector <| Pop)

popTo : Scene -> Cmd Msg
popTo = send << WizardVector << PopTo

replaceWith : Scene -> Cmd Msg
replaceWith = send << WizardVector << ReplaceWith

rebaseTo : Scene -> Cmd Msg
rebaseTo = send << WizardVector << RebaseTo

rebase : Cmd Msg
rebase = send <| WizardVector <| Rebase

msgForReset : Msg
msgForReset = WizardVector <| Reset

sceneIsVisible : KioskModel a -> Scene -> Bool
sceneIsVisible model scene = (currentScene model) == scene

currentScene : KioskModel a -> Scene
currentScene model =
  List.Nonempty.head model.sceneStack

{-| For values that can be automatically generated or manually entered. Such
    values will begin as Auto and may be automatically regenerated as long as
    they remain Auto. Once the user provides a value, they become Manual and
    should no longer be automatically manipulated. -}
type AutoMan a
  = Auto a
  | Manual a


-----------------------------------------------------------------------------
-- VIEW UTILITIES
-----------------------------------------------------------------------------

option_NoTabIndex = Options.attribute <| tabindex <| -99

sceneFrame : KioskModel a -> List (Html Msg) -> Html Msg
sceneFrame model sceneHtml =
  div [frameDivStyle]
    [ img [src model.flags.bannerTopUrl, bannerTopStyle] []
    , div [sceneDivStyle] sceneHtml
    , frameNavButtons model
    , img [src model.flags.bannerBottomUrl, bannerBottomStyle] []
    ]

frameNavButtons : KioskModel a -> Html Msg
frameNavButtons model =
  let
    isBaseScene = List.Nonempty.isSingleton model.sceneStack
  in
    div [navDivStyle]
      [ Button.render MdlVector [10000] model.mdl
          ( [ Button.flat
            , Options.disabled isBaseScene
            , Options.onClick (WizardVector <| Pop)
            , option_NoTabIndex
            ]
            ++navButtonCss
          )
          [text "Back"]
      , hspace 600
      , Button.render MdlVector [10001] model.mdl
          ( [ Button.flat
            , Options.onClick (WizardVector <| Reset)
            , option_NoTabIndex
            ]
            ++navButtonCss
          )
          [text "Quit"]
      ]


genericScene : KioskModel a -> String -> String -> Html Msg -> List (ButtonSpec Msg) -> List String -> Html Msg
genericScene model title subtitle extraContent buttonSpecs badNews =
  let sceneHtml =
    [ p [sceneTitleStyle] [text title]
    , p [sceneSubtitleStyle] [text subtitle]
    , extraContent
    , vspace 50
    , formatBadNews badNews
    , vspace (if List.isEmpty badNews then 0 else 50)
    , div [] (List.map (sceneButton model) buttonSpecs)
    ]
  in sceneFrame model sceneHtml


blankGenericScene : KioskModel a -> Html Msg
blankGenericScene model =
  genericScene model "" "" (text "") [] []

type alias PadButtonSpec msg = { title : String, msg: msg, colored: Bool }

padButton : KioskModel a -> PadButtonSpec Msg -> Html Msg
padButton model spec =  -- REVIEW: Index 0 is ok because buttons don't have state?
  Button.render MdlVector [0] model.mdl
    (
      [ Button.fab
      , Options.onClick spec.msg
      ]
      ++
      if spec.colored then [Button.colored] else []
    )
    [ text spec.title ]

type alias ButtonSpec msg = { title : String, msg: msg, enabled: Bool }

sceneButton : KioskModel a -> ButtonSpec Msg -> Html Msg
sceneButton model spec =
  Button.render MdlVector [0] model.mdl  -- REVIEW: Index 0 is ok because buttons don't have state?
    ( [ Button.raised
      , Button.colored
      , Options.onClick spec.msg
      , Options.disabled (not spec.enabled)
      , option_NoTabIndex
      ]
      ++sceneButtonCss
    )
    [ text spec.title ]

sceneGenericTextField : KioskModel a -> Index -> String -> String -> (String -> Msg) -> List (Textfield.Property Msg) -> Html Msg
sceneGenericTextField model index hint value msger options =
  Textfield.render MdlVector index model.mdl
    (
      [ Textfield.label hint
      , Textfield.floatingLabel
      , Textfield.value value
      , Options.onInput msger
      , Options.attribute <| tabindex <| List.sum index
      , Options.attribute <| id <| toString index
      , css "width" "500px"
      ]
      ++
      options
    )
    []

sceneTextField : KioskModel a -> Index -> String -> String -> (String -> Msg) -> Html Msg
sceneTextField model index hint value msger =
  sceneGenericTextField model index hint value msger []

scenePasswordField : KioskModel a -> Index -> String -> String -> (String -> Msg) -> Html Msg
scenePasswordField model index hint value msger =
  sceneGenericTextField model index hint value msger [Textfield.password]

sceneEmailField : KioskModel a -> Index -> String -> String -> (String -> Msg) -> Html Msg
sceneEmailField model index hint value msger =
  sceneGenericTextField model index hint value msger [Textfield.email]

sceneTextArea : KioskModel a -> Index -> String -> String -> Int -> (String -> Msg) -> Html Msg
sceneTextArea model index hint value numRows msger =
  sceneGenericTextField model index hint value msger [Textfield.textarea, Textfield.rows numRows]

sceneCheckbox : KioskModel a -> Index -> String -> Bool -> Msg -> Html Msg
sceneCheckbox model index label value msger =
  -- Toggle.checkbox doesn't seem to handle centering very well. The following div compensates for that.
  div [style ["text-align"=>"left", "display"=>"inline-block", "width"=>"400px"]]
    [ Toggles.checkbox MdlVector index model.mdl
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

redSpan : List (Html Msg) -> Html Msg
redSpan inner =
  span [style ["color"=>"red"]] inner


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

(=>) = (,)

px : Int -> String
px num = (toString num) ++ "px"

pt : Int -> String
pt num = (toString num) ++ "pt"

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

sceneTextStyle = style
  [ "font-size" => "22pt"
  , "line-height" => "1em"
  ]

sceneTextBlockStyle = style
  [ "padding-left" => px 100
  , "padding-right" => px 100
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

userIdStyle = style
  [ "margin" => "10px"
  , "padding" => "10px"
  , "background-color" => "#ccffff" -- light cyan
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

textAreaColor = "rgb(102,153,204,.2)"  -- This is a websafe color, with alpha.