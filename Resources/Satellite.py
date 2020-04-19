from overrides import overrides

from IdeaSim.Simulation import Simulation
from Resources.ActionType import ActionType
from Task import Item, Task
from Resources.Movement import MovableResource, Position
from IdeaSim.Resources import Performer


class Satellite(MovableResource, Performer):
    def __init__(self, env, position, acc, max_v, par):
        MovableResource.__init__(self, env, position, acc, max_v, par)
        Performer.__init__(self, env)
        self.env = env
        self.position = position
        self.position = position
        self.TIME_TO_DROP_TO_CHANNEL = 10
        self.TIME_TO_PICKUP_FROM_CHANNEL = 10
        self.TIME_TO_DROP_TO_BAY = 10
        self.TIME_TO_PICKUP_FROM_BAY = 10
        self.weight = par.Wsa
        self.add_mapping(ActionType.MOVE, self.move_satellite)
        self.add_mapping(ActionType.PICKUP, self.pickup)
        self.add_mapping(ActionType.DROP, self.drop)
        self.add_mapping(ActionType.DROP_TO_BAY, self.drop_to_bay)
        self.add_mapping(ActionType.GET_FROM_BAY, self.get_from_bay)

        self.monitor = self.sim.get_status().monitor
        self.util = 0

    @overrides
    def __str__(self):
        return "Satellite(" + str(self.id) + ")"

    @overrides
    def __weight__(self):
        return self.weight + (self.content.weight if self.content is not None else 0)

    def go_to(self, z):
        time = self.move(self.sim, Position(self.position.section, self.position.level, self.position.x, z),
                         self.sim.get_status().parameter)
        self.util += time
        return self.env.timeout(
            time)

    def move_satellite(self, action, sim, taken_inf):
        assert (isinstance(sim, Simulation))
        if "resource" in action.param:
            action.param["z"] = sim.find_res_by_id(action.param["resource"], free=False)[
                0].position.level
        yield self.go_to(action.param["z"])
        return

    def pickup(self, action, sim, taken_inf):
        assert (isinstance(sim, Simulation))
        self.content = list(filter(lambda x: x.id == action.param["channel_id"], taken_inf))[0].items.pop()
        if not isinstance(self.content, Item.Item):
            raise Performer.IllegalAction("Satellite pickup non Item")
        self.util += self.TIME_TO_PICKUP_FROM_CHANNEL
        yield self.env.timeout(self.TIME_TO_PICKUP_FROM_CHANNEL)
        return

    def drop(self, action, sim, taken_inf):
        assert (isinstance(sim, Simulation))
        yield list(filter(lambda x: x.id == action.param["channel_id"], taken_inf))[0].put(self.content)
        if self.content is None:
            raise Performer.IllegalAction("Satellite drop None Item to channel")
        self.content = None
        self.util += self.TIME_TO_DROP_TO_CHANNEL
        yield self.env.timeout(self.TIME_TO_DROP_TO_CHANNEL)
        return

    def drop_to_bay(self, action, sim, taken_inf):
        if self.content is None:
            raise Performer.IllegalAction("Satellite drop None Item to bay")
        self.content = None
        self.util += self.TIME_TO_DROP_TO_BAY
        yield self.env.timeout(self.TIME_TO_DROP_TO_BAY)
        return

    def get_from_bay(self, action, sim, taken_inf):
        self.content = action.param["item"]
        if not isinstance(self.content, Item.Item):
            raise Performer.IllegalAction("Satellite pickup non Item from bay")
        self.util += self.TIME_TO_PICKUP_FROM_BAY
        yield self.env.timeout(self.TIME_TO_PICKUP_FROM_BAY)
        return
