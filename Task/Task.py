import itertools
from enum import Enum

from Task.Item import Item


class OrderType(Enum):
    DEPOSIT = 1
    RETRIEVAL = 2


class Task:
    newid = itertools.count()

    def __init__(self, item, order_type):
        self.order_type = order_type
        self.id = next(self.newid)
        self.item = item
        assert isinstance(item, Item)

    def __str__(self) -> str:
        return str(self.id) + "->" + str(self.item) + ("R" if self.order_type == OrderType.RETRIEVAL else "D")
