
module PublicHoursScene exposing
  ( init
  , update
  , view
  , PublicHoursModel
  )

-- Standard
import Html exposing (..)
import Html.Attributes exposing (..)
import Regex exposing (regex)
import Time exposing (Time)
import Date exposing (Date)

-- Third Party
import String.Extra exposing (..)
import Material
import List.Nonempty exposing (Nonempty)

-- Local
import XerocraftApi as XcApi
import XisRestApi as XisApi exposing (..)
import Wizard.SceneUtils exposing (..)
import Types exposing (..)


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  { a
  ------------------------------------
  | mdl : Material.Model
  , flags : Flags
  , sceneStack : Nonempty Scene
  ------------------------------------
  , publicHoursModel : PublicHoursModel
  , xisSession : XisApi.Session Msg
  }



type alias PublicHoursModel =
  -------------- Req'd arguments:
  { member : Maybe Member
  -------------- Other state:
  , badNews : List String
  }


init : Flags -> (PublicHoursModel, Cmd Msg)
init flags =
  let sceneModel =
    { member = Nothing
    , badNews = []
    }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : PublicHoursMsg -> KioskModel a -> (PublicHoursModel, Cmd Msg)
update msg kioskModel =

  let
    sceneModel = kioskModel.publicHoursModel
    xis = kioskModel.xisSession

  in case msg of

    PH_Segue member ->
      let
        newSceneModel =
          { sceneModel
          | member = Just member
          }
      in
        (newSceneModel, send <| WizardVector <| Push PublicHours)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.publicHoursModel
    xis = kioskModel.xisSession
  in
    genericScene kioskModel
      "Our Public Access Hours"
      "There's No Cost to Attend!"
      -- TODO: This should eventually be generated from time block info.
      ( div [sceneTextStyle, sceneTextBlockStyle]
         [ vspace 40
         , (span [circleStyle] [text "1"]), vspace 0
         , text "Thursdays from 7pm to 10pm", vspace 0
         , text "Everybody is Welcome"
         , vspace 40
         , (span [circleStyle] [text "2"]), vspace 0
         , text "Saturdays from noon to 4pm", vspace 0
         , text "Everybody is Welcome"
         , vspace 40
         , (span [circleStyle] [text "3"]), vspace 0
         , text "Tuesdays from 6pm to 10pm", vspace 0
         , text "Women/Trans/Femme Only"
         , vspace 20
         ]
      )
      [ ButtonSpec "OK" (WizardVector <| Reset) True ]
      []  -- No bad news.


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

circleStyle = style
  [ "background" => "#5EA226"
  , "border-radius" => "0.8em"
  , "-moz-border-radius" => "0.8em"
  , "-webkit-border-radius" => "0.8em"
  , "color" => "#ffffff"
  , "display" => "inline-block"
  , "font-weight" => "bold"
  , "line-height" => "1.6em"
  , "margin-right" => "15px"
  , "text-align" => "center"
  , "width" => "1.6em"
  ]
