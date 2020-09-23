from enum import Enum

from overrides import overrides
from simpy import Store
from IdeaSim.Resources import Resource
from Resources.Lift import Lift


class LifoStore(Store):
    def __init__(self, env, capacity):
        super().__init__(env, capacity)

    def _do_put(self, event):
        if len(self.items) < self._capacity:
            self.items.insert(0, event.item)
            event.succeed()
        else:
            raise Exception("exciting capacity")


class Channel(LifoStore, Resource):
    class Orientations(Enum):
        LEFT = 0
        RIGHT = 1

    def __init__(self, env, capacity, lift, position, orientation):
        Store.__init__(self, env, capacity)
        Resource.__init__(self, env)
        self.position = position
        self.lift = lift
        self.orientation = orientation
        assert isinstance(lift, Lift)

    def first_item_z_position(self):
        n = self.capacity - len(self.items)
        return n if self.orientation == self.Orientations.LEFT else -n

    @overrides
    def __str__(self):
        return "channel(" + str(self.position) + ")"
