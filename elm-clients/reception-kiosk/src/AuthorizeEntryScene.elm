
module AuthorizeEntryScene exposing
  ( init
  , update
  , view
  , AuthorizeEntryModel
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
import CalendarDate
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
  , sceneStack : Nonempty Scene
  ------------------------------------
  , authorizeEntryModel : AuthorizeEntryModel
  , currTime : Time
  , xisSession : XisApi.Session Msg
  }


type alias AuthorizeEntryModel =
  -------------- Req'd arguments:
  { member : Maybe Member
  -------------- Other state:
  , badNews : List String
  }


init : Flags -> (AuthorizeEntryModel, Cmd Msg)
init flags =
  let sceneModel =
    { member = Nothing
    , badNews = []
    }
  in (sceneModel, Cmd.none)


-----------------------------------------------------------------------------
-- UPDATE
-----------------------------------------------------------------------------

{- Will keep this simple, for now. This scene will appear if all of the following are true:
   (1) We know what type of time block we're in.
   (2) The time block is tagged as being for Supporting Members Only.
   (3) We have the user's membership info.
-}
membersOnlyButNotMember :
  XisApi.Session a -> Member -> PointInTime -> Maybe TimeBlock -> List TimeBlockType -> Bool
membersOnlyButNotMember
  xis member now nowBlock allTypes =

  let
    membersOnlyStr = "Members Only"
    defaultBlockTypeName = case xis.defaultBlockType allTypes of
      Just bt -> bt.data.name
      Nothing -> ""
    isCurrent = case member.data.latestNonfutureMembership of
      Just m -> xis.coverTime [m] now
      Nothing -> False
    isMembersOnly = case nowBlock of
      Just nb -> xis.blockHasType membersOnlyStr allTypes nb
      Nothing -> defaultBlockTypeName == membersOnlyStr
  in
    isMembersOnly && not isCurrent


update : AuthorizeEntryMsg -> KioskModel a -> (AuthorizeEntryModel, Cmd Msg)
update msg kioskModel =

  let
    sceneModel = kioskModel.authorizeEntryModel
    xis = kioskModel.xisSession

  in case msg of

    AE_Segue member nowBlock allTypes ->

      let
        newSceneModel = { sceneModel | member = Just member }
      in
        if membersOnlyButNotMember xis member kioskModel.currTime nowBlock allTypes then
          (newSceneModel, send <| YouCantEnterVector <| YCE_Segue member)
        else
          -- Nothing to say, so skip this scene.
          (newSceneModel, send <| OldBusinessVector <| OB_SegueA CheckInSession member)


-----------------------------------------------------------------------------
-- VIEW
-----------------------------------------------------------------------------

view : KioskModel a -> Html Msg
view kioskModel =
  let
    sceneModel = kioskModel.authorizeEntryModel
    xis = kioskModel.xisSession
  in
    errorView kioskModel "AuthorizeEntryScene should never be on the scene stack."


-----------------------------------------------------------------------------
-- STYLES
-----------------------------------------------------------------------------