from overrides import overrides

from Resources.Resources import Resource
from Resources.Movement import MovableResource, Position
from Resources.Performer import Performer
from Manager.Action import ActionType
from Resources.Shuttle import Shuttle
from SimMain.Logger import Logger


class Lift(MovableResource, Performer):
    def __init__(self, env, position, acc, max_v, par):
        MovableResource.__init__(self, position, acc, max_v, par)
        Performer.__init__(self, env, self.id)
        self.env = env
        self.TIME_TO_DROP = 10
        self.TIME_TO_PICKUP = 10
        self.weight = par.Wli

    @overrides
    def __str__(self):
        return "Lift(" + str(self.id) + ")"

    def go_to(self, level):
        return self.env.timeout(
            self.move(Position(self.position.section, level, self.position.x, self.position.z), self.parameter))

    def perform(self, action, taken_inf, all_resources):
        Performer.perform(self, action, taken_inf, all_resources)
        if action.actionType == ActionType.MOVE:
            if "resource" in action.param:
                action.param["level"] = list(filter(lambda x: x.id == action.param["resource"], all_resources))[
                    0].position.level
            yield self.go_to(action.param["level"])
            return
        if action.actionType == ActionType.PICKUP:
            if self.content is not None and self.content.id == action.param["shuttle"]:
                return
            elif self.content is not None:
                raise Performer.IllegalAction("Lift full before pickup")
            self.content = list(filter(lambda x: x.id == action.param["shuttle"], taken_inf))[0]
            if self.content is None:
                raise Performer.IllegalAction("Lift getting None item")
            yield self.env.timeout(self.TIME_TO_PICKUP)
            return
        if action.actionType == ActionType.DROP:
            if self.content is None:
                self.content = None
                return
            if not isinstance(self.content, Shuttle):
                raise Performer.IllegalAction("Lift drop not shuttle")
            if self.content is None:
                self.content = None
            self.content.position.level = self.position.level
            self.content.position.x = 0
            self.content = None
            yield self.env.timeout(self.TIME_TO_DROP)
            return
