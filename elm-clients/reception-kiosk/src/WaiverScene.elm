
port module WaiverScene exposing
  ( init
  , sceneWillAppear
  , update
  , view
  , subscriptions
  , WaiverModel
  )

-- Standard
import Html exposing (..)
import Html.Attributes exposing (..)
import Regex exposing (regex)

-- Third Party
import Material
import List.Nonempty exposing (Nonempty)

-- Local
import Wizard.SceneUtils exposing (..)
import Types exposing (..)

-----------------------------------------------------------------------------
-- INIT
-----------------------------------------------------------------------------

-- These type aliases describes the type of kiosk model that this scene requires.
type alias KioskModel a =
  { a
  ------------------------------------
  | mdl : Material.Model
  , flags : Flags
  , sceneStack : Nonempty Scene
  ------------------------------------
  , waiverModel : WaiverModel
  }


type alias WaiverModel =
  ------------ REQ'D ARGS:
  { methods : Maybe (List Int)
  , firstName : Maybe String
  , lastName : Maybe String
  , email : Maybe String
  , isAdult : Maybe Bool
  , userName : Maybe String
  , password : Maybe String
  ------------ OTHER STATE:
  , isSigning : Bool
  , signature : String  -- This is a data URL
  , badNews : List String
  }


-- The args we need from the previous scene, pulled from the scene model.
-- Many of these are required only so we can push them to the next scene.
args m =
  ( m.methods
  , m.firstName
  , m.lastName
  , m.email
  , m.isAdult
  , m.userName
  , m.password
  )

init : Flags -> (WaiverModel, Cmd Msg)
init flags =
  let sceneModel =
    ------------ We start with no args. They come in through SEGUE
    { methods = Nothing
    , firstName = Nothing
    , lastName = Nothing
    , email = Nothing
    , isAdult = Nothing
    , userName = Nothing
    , password = Nothing
    ------------ Other state:
    , isSigning = False
    , signature = ""
    , badNews = []
    }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- PORTS
-----------------------------------------------------------------------------

port initSignaturePad : (String, String) -> Cmd msg  -- 1) ID of canvas to be used, 2) data URL of image or ""
port clearSignaturePad : String -> Cmd msg
port sendSignatureImage : String -> Cmd msg  -- "image/png", "image/jpeg", or "image/svg+xml"
port signatureImage : (String -> msg) -> Sub msg  -- requested signature data arrives via this port

-----------------------------------------------------------------------------
-- SCENE WILL APPEAR
-----------------------------------------------------------------------------

sceneWillAppear : KioskModel a -> Scene -> (WaiverModel, Cmd Msg)
sceneWillAppear kioskModel appearingScene =
  if appearingScene == Waiver
    then
      let sceneModel = kioskModel.waiverModel
      in ({sceneModel | isSigning=False}, Cmd.none)
    else
      (kioskModel.waiverModel, Cmd.none)

-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

update : WaiverMsg -> KioskModel a -> (WaiverModel, Cmd Msg)
update msg kioskModel =
  let sceneModel = kioskModel.waiverModel
  in case msg of

    WVR_Segue (methods, fname, lname, email, adult, uname, pw) ->
      ( { sceneModel
        | methods = Just methods
        , firstName = Just fname
        , lastName = Just lname
        , email = Just email
        , isAdult = Just adult
        , userName = Just uname
        , password = Just pw
        }
      , send <| WizardVector <| Push <| Waiver
      )

    ShowSignaturePad canvasId ->
      ({sceneModel | isSigning=True}, initSignaturePad (canvasId, sceneModel.signature))

    ClearSignaturePad canvasId ->
      (sceneModel, clearSignaturePad canvasId)

    GetSignature ->
      (sceneModel, sendSignatureImage "image/png")

    UpdateSignature dataUrl ->
      case args sceneModel of

        (Just wdyh, Just fn, Just ln, Just email, Just adult, Just uname, Just pw) ->
          ( {sceneModel | signature = dataUrl}
          , send
              <| CreatingAcctVector
              <| CA_Segue (wdyh, fn, ln, email, adult, uname, pw, dataUrl)
          )

        _ ->
          ( {sceneModel | signature = dataUrl}
          , send <| ErrorVector <| ERR_Segue missingArguments
          )


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  -- TODO: Don't present this to minors.
  -- TODO: Don't present this to people who have already signed.
  let sceneModel = kioskModel.waiverModel
  in genericScene kioskModel
    ("Be Careful at " ++ kioskModel.flags.orgName ++ "!")
    "Please read and sign the following waiver"
    (div []
      [ vspace 20
      , div [id "waiver-box", waiverBoxStyle sceneModel.isSigning] waiverHtml
      , div [style ["display"=>if sceneModel.isSigning then "block" else "none"]]
          [ canvas [width 760, height 200, id "signature-pad", signaturePadStyle] [] ]
      ]
    )
    ( if sceneModel.isSigning then
        [ ButtonSpec "Accept" (WaiverVector <| GetSignature) True
        , ButtonSpec "Clear" (WaiverVector <| ClearSignaturePad <| "signature-pad") True
        ]
      else
        [ ButtonSpec "Sign" (WaiverVector <| ShowSignaturePad <| "signature-pad") True
        ]
    )
    sceneModel.badNews

-----------------------------------------------------------------------------
-- SUBSCRIPTIONS
-----------------------------------------------------------------------------

subscriptions: KioskModel a -> Sub Msg
subscriptions model =
  Sub.batch
    [
        signatureImage (WaiverVector << UpdateSignature)
    ]

-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------

waiverBoxStyle isSigning = style
  [ "height" => if isSigning then "200px" else "600px"
  , "overflow-y" => "scroll"
  , "margin-left" => "20px"
  , "margin-right" => "20px"
  , "border" => "1px solid #bbbbbb"
  , "font-size" => "16pt"
  , "padding" => "5px"
  ]

signaturePadStyle = style
  [ "height" => "200px"
  , "width" => "760px"
  , "border" => "1px solid #bbbbbb"
  , "cursor" => "crosshair"
  , "touch-action" => "none"
  , "margin-top" => "50px"
  , "margin-bottom" => "50px"
  ]

-----------------------------------------------------------------------------
-- Should be in external HTML files
-----------------------------------------------------------------------------

waiverHtml : List (Html Msg)
waiverHtml =
  [ p [style ["font-size"=>"20pt", "font-weight"=>"bold", "margin-top"=>"10px"]]
      [ text "XEROCRAFT INC. RELEASE AND WAIVER OF LIABILITY, ASSUMPTION OF RISK, AND INDEMNITY CONSENT AGREEMENT"
      , br [] []
      , text "('Agreement')"
      ]
  , div [style ["text-align"=>"left", "margin-top"=>"20px"]]
      [ p [style ["font-size"=>"16pt", "line-height"=>"15pt"]] [ text "IN CONSIDERATION of being permitted to participate in any way in the activities of Xerocraft Inc. I, for myself or personal representatives, assigns, heirs, and next of kin:" ]
      , ol [style ["font-size"=>"16pt", "line-height"=>"15pt"]]
          [ li [style ["margin-bottom"=>"15px"]] [text "ACKNOWLEDGE, agree, and represent that I understand the nature of Xerocraft inc.'s activities and that I am sober, qualified, in good health, and in proper physical and mental condition to participate in such Activity. I further agree and warrant that if at any time I believe conditions to be unsafe, I will immediately discontinue further participation in the Activity." ]
          , li [style ["margin-bottom"=>"15px"]]
              [ text "FULLY UNDERSTAND THAT: (a) "
              , b [] [text "THESE ACTIVITIES MAY INVOLVE RISKS AND DANGERS OF SERIOUS BODILY INJURY, INCLUDING PERMANENT DISABILITY, AND DEATH " ]
              , text "('RISKS'); (b) these Risks and dangers may be caused by my own actions or inaction's, the actions or inaction's of others participating in the Activity, the condition(s) under which the Activity takes place, or THE NEGLIGENCE OF THE 'RELEASEES' NAMED BELOW; (c) there may be OTHER RISK AND SOCIAL AND ECONOMIC LOSSES either not known to me or not readily foreseeable at this time; and I FULLY ACCEPT AND ASSUME ALL SUCH RISKS AND ALL RESPONSIBILITY FOR LOSSES, COSTS, AND DAMAGES I incur as a result of my participation or that of the minor in the Activity."
              ]
          , li [] [text "HEREBY RELEASE, DISCHARGE, AND COVENANT NOT TO SUE Xerocraft inc., their respective administrators, directors, agents, officers, members, volunteers, and employees, other participants, any sponsors, advertisers, and, if applicable, owner(s) and lessors of premises on which the Activity takes place, (each considered one of the 'RELEASEES' herein) FROM ALL LIABILITY, CLAIMS, DEMANDS, LOSSES, OR DAMAGES ON OR BY MY ACCOUNT CAUSED OR ALLEGED TO BE CAUSED IN WHOLE OR IN PART BY THE NEGLIGENCE OF THE 'RELEASEES' OR OTHERWISE, INCLUDING NEGLIGENT RESCUE OPERATIONS AND I FURTHER AGREE that if, despite this RELEASE AND WAIVER OF LIABILITY, ASSUMPTION OF RISK, AND INDEMNITY AGREEMENT I, or anyone on my behalf, makes a claim against any of the Releasees, I WILL INDEMNIFY, SAVE, AND HOLD HARMLESS EACH OF THE RELEASEES from any litigation expenses, attorney fees, loss, liability, damage, or cost which may incur as the result of such claim. I have read this Agreement, fully understand its terms, understand that I have given up substantial rights by signing it and have signed it freely and without inducement or assurance of any nature and intend it to be a complete and unconditional release of all liability to the greatest extent allowed by law and agree that if any portion of this Agreement is held to be invalid the balance, notwithstanding, shall continue in full force and effect." ]
          ]
      , p [style ["font-size"=>"16pt", "line-height"=>"15pt"]]
          [ b [] [text "MINOR RELEASE."]
          , text "The minor's parent and/or legal guardian, understand the nature of Xerocraft inc.'s activities and the minor's experience and capabilities and believe the minor to be qualified, in good health, and in proper physical and mental condition to participate in such activity. I hereby release, discharge, covenant not to sue, and agree to indemnify and save and hold harmless each of the releasee's from all liability claims, demands, losses, or damages on the minor's account caused or alleged to be caused in whole or in part by the negligence of the 'releasees' or otherwise, including negligent rescue operation and further agree that if, despite this release, I, the minor, or anyone on the minor's behalf makes a claim against any of the releasees named above, I will indemnify, save, and hold harmless each of the releasees from any litigation expenses, attorney fees, loss liability, damage, or any cost which may incur as the result of any such claim."
          ]
      ]
  ]
