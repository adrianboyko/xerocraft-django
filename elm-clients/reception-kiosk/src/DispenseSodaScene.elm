
module DispenseSodaScene exposing
  ( init
  , update
  , view
  , DispenseSodaModel
  )

-- Standard
import Html exposing (Html, div, text, img, br)
import Html.Attributes exposing (src, width, style)

-- Third Party
import Material
import Material.Button as Button
import Material.Options as Options
import List.Nonempty as NonEmpty

-- Local
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import XisRestApi as XisApi exposing (Member)
import PointInTime exposing (PointInTime)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  { a
  ------------------------------------
  | mdl : Material.Model
  , flags : Flags
  , sceneStack : NonEmpty.Nonempty Scene
  ------------------------------------
  , currTime : PointInTime
  , dispenseSodaModel : DispenseSodaModel
  , xisSession : XisApi.Session Msg
  }

type alias DispenseSodaModel =
  { member : Maybe Member
  }


init : Flags -> (DispenseSodaModel, Cmd Msg)
init flags = (
  { member = Nothing
  }
  ,
  Cmd.none
  )


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : DispenseSodaMsg -> KioskModel a -> (DispenseSodaModel, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.dispenseSodaModel
    xis = kioskModel.xisSession

  in case msg of

    DS_Segue member ->
      ( {sceneModel | member = Just member}
      , send <| WizardVector <| Push <| DispenseSoda
      )

    DS_Dispense member productId ->
      let
        newVendLog =
          { whoFor = xis.memberUrl member.id
          , product = xis.productUrl productId
          , when = kioskModel.currTime
          }
        tagger = DispenseSodaVector << DS_Dispense_Result
      in
        ( sceneModel
        , xis.createVendLog newVendLog tagger
        )

    DS_Dispense_Result (Ok _) ->
      (sceneModel, Cmd.none)

    DS_Dispense_Result (Err error) ->
      (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    button = sceneButton kioskModel
    sceneModel = kioskModel.dispenseSodaModel
    friendlyName =
      Maybe.withDefault "ERR"
        <| Maybe.map (.data >> .friendlyName) sceneModel.member
  in
    case sceneModel.member of

      Just m ->
        genericScene kioskModel
        ("Ok, "++ friendlyName ++"!")
        "The following drinks are available:"
        (div [sceneTextStyle]
          [ vspace 100

          , ( Button.render MdlVector [1,1] kioskModel.mdl
                (canButtonOptions m 6)
                [img [src "/static/soda/CokeClassic.png", canImgStyle] []]
            )
          , ( Button.render MdlVector [1,2] kioskModel.mdl
                (canButtonOptions m 1)
                [img [src "/static/soda/DietCoke.png", canImgStyle] []]
            )
          , ( Button.render MdlVector [1,3] kioskModel.mdl
                (canButtonOptions m 4)
                [img [src "/static/soda/DrPepper.gif", canImgStyle] []]
            )
          , vspace 0
          , ( Button.render MdlVector [1,4] kioskModel.mdl
                (canButtonOptions m 2)
                [img [src "/static/soda/MountainDew.png", canImgStyle] []]
            )
          , ( Button.render MdlVector [1,5] kioskModel.mdl
                (canButtonOptions m 5)
                [img [src "/static/soda/RefresheSeltzer.png", canImgStyle] []]
            )
          , ( Button.render MdlVector [1,6] kioskModel.mdl
                (canButtonOptions m 3)
                [img [src "/static/soda/Squirt.png", canImgStyle] []]
            )
          ]
        )
        []  -- Buttons are woven into the content of the welcome text.
        []  -- Never any bad news for this scene.

      Nothing ->
        errorView kioskModel "Required args not received"


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

canButtonOptions member productId =
  [ Button.ripple
  , Button.accent
  , Options.onClick (DispenseSodaVector <| DS_Dispense member productId)
  , Options.css "height" (px 180)
  , Options.css "padding" (px 0)
  ]

canImgStyle = style
  [ "height" => px 150
  , "width"  => px 79
  , "margin-top" => px 15
  , "margin-bottom" => px 15
  , "margin-left" => px 25
  , "margin-right" => px 25
  ]

