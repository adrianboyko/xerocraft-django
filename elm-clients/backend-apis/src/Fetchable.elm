module Fetchable exposing (..)

type Fetchable a
  = Pending
  | Received a
  | Failed String

received : Fetchable a -> Bool
received x =
  case x of
    Received _ -> True
    _ -> False

map : (a -> b) -> Fetchable a -> Fetchable b
map xform fetchable =
  case fetchable of
    Pending -> Pending  -- Interesting case because it should not be attempted.
    Received x -> Received (xform x)
    Failed str -> Failed str

withDefault : a -> Fetchable a -> a
withDefault default fetchable =
  case fetchable of
    Pending -> default  -- Interesting case because it should not be attempted.
    Received x -> x
    Failed str -> default
