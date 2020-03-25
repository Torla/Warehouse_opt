from overrides import overrides

from IdeaSim.Simulation import Simulation
from Resources.ActionType import ActionType
from Resources.Movement import MovableResource, Position
from IdeaSim.Resources import Performer
from Resources.Shuttle import Shuttle


class Lift(MovableResource, Performer):
    def __init__(self, env, position, acc, max_v, par):
        MovableResource.__init__(self, env, position, acc, max_v, par)
        Performer.__init__(self, env)
        self.position = position
        self.env = env
        self.TIME_TO_DROP = 10
        self.TIME_TO_PICKUP = 10
        self.weight = par.Wli
        self.add_mapping(ActionType.MOVE, self.move_lift)
        self.add_mapping(ActionType.PICKUP, self.pickup)
        self.add_mapping(ActionType.DROP, self.drop)

    @overrides
    def __str__(self):
        return "Lift(" + str(self.id) + ")"

    def go_to(self, level):
        return self.env.timeout(
            self.move(self.env, Position(self.position.section, level, self.position.x, self.position.z),
                      self.sim.get_status().parameter))

    def move_lift(self, action, sim, taken_inf):
        assert (isinstance(sim, Simulation))
        if "resource" in action.param:
            action.param["level"] = sim.find_res_by_id(action.param["resource"], free=False)[
                0].position.level
        yield self.go_to(action.param["level"])
        return

    def pickup(self, action, sim, taken_inf):
        assert (isinstance(sim, Simulation))
        if self.content is not None and self.content.id == action.param["shuttle"]:
            return
        elif self.content is not None:
            raise Performer.IllegalAction("Lift full before pickup")
        self.content = list(filter(lambda x: x.id == action.param["shuttle"], taken_inf))[0]
        if self.content is None:
            raise Performer.IllegalAction("Lift getting None item")
        yield self.env.timeout(self.TIME_TO_PICKUP)
        return

    def drop(self, action, sim, taken_inf):
        assert (isinstance(sim, Simulation))
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

    def perform(self, action, taken_inf):
        Performer.perform(self, action, taken_inf)
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
