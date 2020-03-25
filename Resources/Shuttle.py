from overrides import overrides

from Resources.Movement import MovableResource, Position
from IdeaSim.Resources import Performer
from Resources.Satellite import Satellite


class Shuttle(MovableResource, Performer):
    def __init__(self, env, position, acc, max_v, par):
        MovableResource.__init__(self, env, position, acc, max_v, par)
        Performer.__init__(self, env)
        self.env = env
        self.position = position
        self.TIME_TO_DROP = 10
        self.TIME_TO_PICKUP = 10
        self.weight = par.Wsh

    @overrides
    def __str__(self):
        return "Shuttle(" + str(self.id) + ")"

    def go_to(self, x):
        return self.env.timeout(
            self.move(Position(self.position.section, self.position.level, x, self.position.z), self.parameter))

    def perform(self, action, taken_inf, all_resources):
        # todo better error
        Performer.perform(self, action, taken_inf, all_resources)
        if action.actionType == ActionType.MOVE:
            if "resource" in action.param:
                action.param["x"] = list(filter(lambda x: x.id == action.param["resource"], all_resources))[
                    0].position.x
            yield self.go_to(action.param["x"])
            return
        if action.actionType == ActionType.PICKUP:
            if action.actionType == ActionType.PICKUP:
                if self.content is not None and self.content.id == action.param["satellite"]:
                    raise Performer.IllegalAction("No satellite to pickup")
                elif self.content is not None:
                    raise Performer.IllegalAction("Shuttle full before pickup")
            self.content = self.content = list(filter(lambda x: x.id == action.param["satellite"], taken_inf))[0]
            if not isinstance(self.content, Satellite):
                raise Performer.IllegalAction("Shuttle pickup non Satellite")
            yield self.env.timeout(self.TIME_TO_DROP)
            return
        if action.actionType == ActionType.DROP:
            if self.content is None:
                return
            self.content.position.level = self.position.level
            self.content.position.x = self.position.x
            self.content.position.z = 0
            self.content = None
            yield self.env.timeout(self.TIME_TO_DROP)
            return
