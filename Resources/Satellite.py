from overrides import overrides

from Task import Item
from Resources.Movement import MovableResource, Position
from IdeaSim.Resources import Performer
from SimMain.Logger import Logger


class Satellite(MovableResource, Performer):
    def __init__(self, env, position, acc, max_v, par):
        MovableResource.__init__(self, env, position, acc, max_v, par)
        Performer.__init__(self, env)
        self.env = env
        self.TIME_TO_DROP_TO_CHANNEL = 10
        self.TIME_TO_PICKUP_FROM_CHANNEL = 10
        self.TIME_TO_DROP_TO_BAY = 10
        self.TIME_TO_PICKUP_FROM_BAY = 10
        self.weight = par.Wsa

    @overrides
    def __str__(self):
        return "Satellite(" + str(self.id) + ")"

    @overrides
    def __weight__(self):
        return self.weight + (self.content.weight if self.content is not None else 0)

    def go_to(self, z):
        return self.env.timeout(
            self.move(Position(self.position.section, self.position.level, self.position.x, z),
                      self.parameter))

    def perform(self, action, taken_inf, all_resources):
        Performer.perform(self, action, taken_inf, all_resources)
        if action.actionType == ActionType.MOVE:
            if "resource" in action.param:
                action.param["z"] = list(filter(lambda x: x.id == action.param["resource"], all_resources))[
                    0].position.z
            yield self.go_to(action.param["z"])
            return
        if action.actionType == ActionType.PICKUP:  # From channel
            self.content = yield list(filter(lambda x: x.id == action.param["channel_id"], taken_inf))[0].get()
            if not isinstance(self.content, Item):
                raise Performer.IllegalAction("Satellite pickup non Item")
            yield self.env.timeout(self.TIME_TO_PICKUP_FROM_CHANNEL)
            return
        if action.actionType == ActionType.GET_FROM_BAY:
            self.content = action.param["item"]
            if not isinstance(self.content, Item):
                raise Performer.IllegalAction("Satellite pickup non Item from bay")
            yield self.env.timeout(self.TIME_TO_PICKUP_FROM_BAY)
            return
        if action.actionType == ActionType.DROP_TO_BAY:
            if self.content is None:
                raise Performer.IllegalAction("Satellite drop None Item to bay")
            self.content = None
            yield self.env.timeout(self.TIME_TO_DROP_TO_BAY)
            return
        if action.actionType == ActionType.DROP:
            yield list(filter(lambda x: x.id == action.param["channel_id"], taken_inf))[0].put(self.content)
            if self.content is None:
                raise Performer.IllegalAction("Satellite drop None Item to channel")
            self.content = None
            yield self.env.timeout(self.TIME_TO_DROP_TO_CHANNEL)
            return
