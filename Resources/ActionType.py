from enum import Enum


class ActionType(Enum):
    MOVE = 1
    GET_FROM_BAY = 3
    DROP_TO_BAY = 4
    PICKUP = 6
    DROP = 7
    BLOCK = 8
    FREE = 9