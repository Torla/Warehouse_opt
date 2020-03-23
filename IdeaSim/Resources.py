import abc
import itertools

from simpy import FilterStore

from IdeaSim import Simulation


class Resources(FilterStore):
    def __init__(self, env, capacity=float('inf')):
        super().__init__(env, capacity)


class Resource:
    new_id = itertools.count()

    def __init__(self, sim):
        assert isinstance(sim, Simulation.Simulation)
        self.sim = sim
        self.id = next(self.new_id)

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
        self.sim.logger.log(str(self) + " perform " + str(action), 7)
        for i in self.action_map[action.actionType](action, self.sim, taken_inf):
            yield i


class Position:
    def __init__(self):
        pass

    def distance(self, pos) -> float:
        raise NotImplementedError("Please Implement this method")

    def __eq__(self, other):
        raise NotImplementedError("Please Implement this method")


class Movable:
    def __init__(self, position, sim):
        self.sim = sim
        self.position = position

    def move(self, position):
        self.sim.logger.log(str(self) + " move from " + str(self.position) + " to " + str(position), 9)
