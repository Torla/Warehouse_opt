import itertools


class Item:
    newid = itertools.count()

    def __init__(self, item_type, weight=1000):
        self.id = next(Item.newid)
        self.item_type = item_type
        self.weight = weight

    def __str__(self) -> str:
        return str(self.item_type) + "(" + str(self.id) + ")"

    def __repr__(self) -> str:
        return str(self.item_type) + "(" + str(self.id) + ") w:" + str(self.weight) + "kg"
