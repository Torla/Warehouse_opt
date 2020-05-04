import abc
import itertools

from simpy import FilterStore

from IdeaSim import Simulation


class Resources(FilterStore):
    def __init__(self, sim, capacity=float('inf')):
        assert (isinstance(sim, Simulation.Simulation))
        super().__init__(sim, capacity)
        self.sim = sim

    def _do_put(self, event):
        super()._do_put(event)
        self.sim.free_map[event.item.id] = True

    def _do_get(self, event):
        for item in self.items:
            if event.filter(item):
                self.items.remove(item)
                event.succeed(item)
                self.sim.free_map[item.id] = False
                break
        return True



class Resource:
    new_id = itertools.count()

    def __init__(self, sim):
        assert isinstance(sim, Simulation.Simulation)
        self.sim = sim
        self.id = next(self.new_id)

        self.blocked_time = 0
        self.last_blocked = None

    def __str__(self) -> str:
        return str(self.id)


class Performer(Resource):
    def __init__(self, sim):
        super().__init__(sim)
        self.action_map = {}

    class IllegalAction(Exception):
        def __init__(self, msg):
            self.msg = msg

    def add_mapping(self, action_type, func):
        self.action_map[action_type] = func

    def perform(self, action, taken_inf):
        try:
            self.sim.logger.log(str(self) + " perform " + str(action), 7)
            for i in self.action_map[action.actionType](action, self.sim, taken_inf):
                yield i
        except Exception as err:
            print(err)
            raise err


class Movable:
    def __init__(self, position, sim):
        self.sim = sim
        self.position = position

    def move(self, position):
        self.sim.logger.log(str(self) + " move from " + str(self.position) + " to " + str(position), 9)
