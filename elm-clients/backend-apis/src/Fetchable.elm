module Fetchable exposing (..)

type Fetchable a
  = Pending
  | Received a
  | Failed String

received x =
  case x of
    Received _ -> True
    _ -> False
