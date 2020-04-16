from overrides import overrides

from IdeaSim.Simulation import Simulation
from Resources.ActionType import ActionType
from Resources.Movement import MovableResource, Position
from IdeaSim.Resources import Performer
from Resources.Satellite import Satellite


class Shuttle(MovableResource, Performer):
    def __init__(self, env, position, acc, max_v, par):
        MovableResource.__init__(self, env, position, acc, max_v, par)
        Performer.__init__(self, env)
        self.position = position
        self.env = env
        self.position = position
        self.TIME_TO_DROP = 10
        self.TIME_TO_PICKUP = 10
        self.weight = par.Wsh
        self.add_mapping(ActionType.MOVE, self.move_shuttle)
        self.add_mapping(ActionType.PICKUP, self.pickup)
        self.add_mapping(ActionType.DROP, self.drop)

        self.monitor = self.sim.get_status().monitor
        self.util = 0

    @overrides
    def __str__(self):
        return "Shuttle(" + str(self.id) + ")"

    def move_shuttle(self, action, sim, taken_inf):
        assert (isinstance(sim, Simulation))
        if "resource" in action.param:
            action.param["x"] = sim.find_res_by_id(action.param["resource"], free=False)[
                0].position.level
        elif "auto" in action.param:
            action.param["x"] = list(filter(lambda x: isinstance(x, Satellite), taken_inf))[0].position.x
        yield self.go_to(action.param["x"])
        return

    def pickup(self, action, sim, taken_inf):
        assert (isinstance(sim, Simulation))
        if self.content is not None and self.content.id == action.param["satellite"]:
            return
        elif self.content is not None:
            raise Performer.IllegalAction("shuttle full before pickup")
        if "satellite" in action.param:
            self.content = list(filter(lambda x: x.id == action.param["satellite"], taken_inf))[0]
        elif "auto" in action.param:
            self.content = list(filter(lambda x: isinstance(x, Satellite), taken_inf))[0]
        if self.content is None:
            raise Performer.IllegalAction("Shuttle getting None item")
        sim.logger.log(str(self.content), 15)
        self.util += self.TIME_TO_PICKUP
        yield self.env.timeout(self.TIME_TO_PICKUP)
        return

    def drop(self, action, sim, taken_inf):
        assert (isinstance(sim, Simulation))
        if self.content is None:
            self.content = None
            return
        if not isinstance(self.content, Satellite):
            raise Performer.IllegalAction("Shuttle drop not shuttle")
        if self.content is None:
            self.content = None
        self.content.position.level = self.position.level
        self.content.position.x = self.position.x
        self.content.position.z = 0
        sim.logger.log(str(self.content), 15)
        self.content = None
        self.util += self.TIME_TO_DROP
        yield self.env.timeout(self.TIME_TO_DROP)
        return

    def go_to(self, x):
        time = self.move(self.env, Position(self.position.section, self.position.level, x, self.position.z),
                         self.sim.get_status().parameter)
        self.util += time
        return self.env.timeout(
            time)


