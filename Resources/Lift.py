from overrides import overrides

from IdeaSim.Simulation import Simulation
from Resources.ActionType import ActionType
from Resources.Movement import MovableResource, Position
from IdeaSim.Resources import Performer
from Resources.Satellite import Satellite
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
        elif "auto" in action.param:
            action.param["level"] = list(filter(lambda x: isinstance(x, Shuttle), taken_inf))[0].position.level
        elif "auto_sat" in action.param:
            action.param["level"] = list(filter(lambda x: isinstance(x, Satellite), taken_inf))[0].position.level
        yield self.go_to(action.param["level"])
        return

    def pickup(self, action, sim, taken_inf):
        assert (isinstance(sim, Simulation))
        if self.content is not None:
            raise Performer.IllegalAction("Lift full before pickup")
        if "shuttle" in action.param:
            self.content = list(filter(lambda x: x.id == action.param["shuttle"], taken_inf))[0]
        elif "auto" in action.param:
            self.content = list(filter(lambda x: isinstance(x, Shuttle), taken_inf))[0]
        if self.content is None:
            raise Performer.IllegalAction("Lift getting None item")
        sim.logger.log(str(self.content), 15)
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
        sim.logger.log(str(self.content), 15)
        self.content = None
        yield self.env.timeout(self.TIME_TO_DROP)
        return
