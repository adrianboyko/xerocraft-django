
module OldBusinessScene exposing (init, sceneWillAppear, update, view, OldBusinessModel)

-- Standard
import Html exposing (Html, div, text, img, br)
import Html.Attributes exposing (src, width, style)

-- Third Party

-- Local
import Wizard.SceneUtils exposing (..)
import Types exposing (..)
import XisRestApi as XisApi exposing (..)
import Fetchable exposing (..)
import CheckInScene exposing (CheckInModel)


-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- This type alias describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  ( SceneUtilModel
    { a
    | oldBusinessModel : OldBusinessModel
    , checkInModel : CheckInModel
    , xisSession : XisApi.Session Msg
    }
  )


type alias OldBusinessModel =
  { oldOpenClaims : Fetchable (List XisApi.Claim)
  }


init : Flags -> (OldBusinessModel, Cmd Msg)
init flags =
  ( { oldOpenClaims = Pending
    }
  , Cmd.none
  )


-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> Scene -> (OldBusinessModel, Cmd Msg)
sceneWillAppear kioskModel appearing vanishing =
  let
    sceneModel = kioskModel.oldBusinessModel
    checkInModel = kioskModel.checkInModel
    xis = kioskModel.xisSession
  in
    case (appearing, vanishing) of

      (OldBusiness, CheckIn) ->
        let
          memberNum = checkInModel.memberNum
          cmd = xis.listClaims
            [ ClaimingMemberEquals memberNum
            , ClaimStatusEquals WorkingClaimStatus
            ]
            (OldBusinessVector << OB_WorkingClaimsResult)
        in
          (sceneModel, cmd)

      (OldBusiness, ReasonForVisit) ->
        -- If we got to ReasonForVisit, there wasn't any old business or user skipped it.
        -- So skip OldBusiness scene on the way back.
        (sceneModel, segueTo CheckIn)

      _ ->
        (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : OldBusinessMsg -> KioskModel a -> (OldBusinessModel, Cmd Msg)
update msg kioskModel =
  let
    sceneModel = kioskModel.oldBusinessModel
    xis = kioskModel.xisSession

  in
    case msg of

      OB_WorkingClaimsResult (Ok {results}) ->
        if List.isEmpty results then
          (sceneModel, segueTo ReasonForVisit)
        else
          ({sceneModel | oldOpenClaims = Received results}, Cmd.none)

      OB_WorkingClaimsResult (Err error) ->
        -- It's not a show stopper if this fails. Just log and move on to next scene.
        let
          _ = Debug.log (toString error)
        in
          (sceneModel, segueTo ReasonForVisit)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.oldBusinessModel
  in
    case sceneModel.oldOpenClaims of

      Received results ->
        let (taskPhrase, sheetPhrase) = phrases results
        in
          genericScene kioskModel
          "Unfinished Business"
          ""
          (div [sceneTextStyle]
            [ vspace 50
            , text ("You previously started " ++ taskPhrase ++ " but")
            , vspace 0
            , text ("didn't complete " ++ sheetPhrase)
            , vspace 0
            , text "Let's do that now so you receive credit!"
            , vspace 20
            ]
          )
          [ ButtonSpec "OK!" (WizardVector <| Push <| TimeSheetPt1)
          , ButtonSpec "Skip" (WizardVector <| Push <| ReasonForVisit)
          ]
          []  -- Never any bad news for this scene.

      _ ->
        blankGenericScene kioskModel

phrases : List XisApi.Claim -> (String, String)
phrases claims =
  let
    n = List.length claims
    nStr = toString n
  in
    if n > 1 then
      (nStr ++ " tasks", "timesheets for them.")
    else
      (nStr ++ " task", "a timesheet for it.")


-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

bottomImgStyle = style
  [ "text-align" => "center"
  , "padding-left" => "30px"
  , "padding-right" => "0"
  ]