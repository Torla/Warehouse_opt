import os

import math

from IdeaSim.Actions import ActionsGraph, Action, Block, Free, GenerateEvent, Branch
from IdeaSim.Event import Event
from IdeaSim.Manager import Manager
from IdeaSim.Resources import Performer, Resource, Resources, Position, Movable
from IdeaSim.Simulation import Simulation
from simpy.resources.container import Container


class Position(Position):

    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y

    def distance(self, pos) -> float:
        return math.sqrt((self.x - pos.x) ** 2 + (self.y - pos.y) ** 2)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


class Well(Resource, Movable):

    def __init__(self, sim, position):
        Resource.__init__(self, sim)
        Movable.__init__(self, position, sim)

    def __str__(self) -> str:
        return "Well " + super().__str__()


class Tank(Performer, Movable):

    def __init__(self, sim, position, capacity):
        Performer.__init__(self, sim)
        Movable.__init__(self, position, sim)
        self.full = Container(sim, capacity)
        Event(sim, sim.now + 1000, "empty_tank" + str(self.id))
        self.sim.manager.add_mapping("empty_tank" + str(self.id), self.empty_tank)
        self.add_mapping("empty", self.__do_empty__)

    def empty_tank(self, event):
        g = ActionsGraph(event.sim)
        b = Block(g, self.id, sort_by=None)
        e = Action(g, "empty", self.id, after=[b.id],
                   condition=lambda x: x.find_res_by_id(self.id, free=False).full.level != 0)
        Free(g, self.id, after=[e.id])

        Event(sim, sim.now + 1000, "empty_tank" + str(self.id))
        return g

    def __do_empty__(self, action, sim, taken_inf):
        yield self.full.get(self.full.level)
        sim.logger.log("empty tank" + str(self.id), 9)

    def is_full(self):
        return self.full.level >= self.full.capacity

    def put_water(self, amount):
        return self.full.put(
            amount if amount + self.full.level <= self.full.capacity else self.full.capacity - self.full.level)

    def __str__(self) -> str:
        return "Tank " + super().__str__()


class Aquifer(Performer, Movable):

    def __init__(self, sim, position):
        Performer.__init__(self, sim)
        Movable.__init__(self, position, sim)
        self.add_mapping("take", self.take)
        self.add_mapping("drop", self.drop)
        Event(sim, 10 + len(sim.all_res), "haul")

    def take(self, action, sim, taken_inf):
        yield sim.wait(10)

    def drop(self, action, sim, taken_inf):
        tank = list(filter(action.param["tank"], taken_inf))[0]
        if tank.is_full():
            Event(sim, sim.now + 1, "haul")
            Action.abort(action, sim)
        tank.put_water(10)
        yield sim.wait(10)

    @staticmethod
    def rain(action, sim):
        Event(sim, sim.now + 1, "haul")
        Action.abort(action, sim)

    @staticmethod
    def haul(event):
        if event.sim.get_status().rain:
            raise Manager.RetryLater()
        g = ActionsGraph(event.sim)
        b = Block(g, lambda x: isinstance(x, Aquifer))
        b1 = Block(g, lambda x: isinstance(x, Well))
        t = Action(g, "take", lambda x: isinstance(x, Aquifer), param={"well": lambda x: isinstance(x, Well)},
                   after=[b.id, b1.id], condition=lambda x: not x.get_status().rain, on_false=Aquifer.rain)
        f1 = Free(g, lambda x: isinstance(x, Well), after=[t.id])
        b1 = Block(g, lambda x: isinstance(x, Tank) and not x.is_full(), sort_by=lambda x: x.full.level,
                   after=[t.id])
        t = Action(g, "drop", lambda x: isinstance(x, Aquifer), param={"tank": lambda x: isinstance(x, Tank)},
                   after=[b1.id])
        f = Free(g, lambda x: isinstance(x, Aquifer), None, after=[t.id])
        f1 = Free(g, lambda x: isinstance(x, Tank), None, after=[t.id, b1.id])
        bh = Branch(g, after=[t.id], condition=lambda x: x.now < 5000)
        GenerateEvent(g, Event(sim, None, "haul"), after=[bh.id], branch=bh.id)
        return g

    def __str__(self) -> str:
        return "Aquifer " + super().__str__()


class Status:
    def __init__(self, sim):
        self.rain = False
        self.sim = sim
        sim.manager.add_mapping("weather", Status.change_of_whether)
        Event(sim, 50, "weather")

    def toggle_rain(self):
        self.rain = not self.rain
        self.sim.logger.log("Rain " + str(self.rain), 6)

    @staticmethod
    def change_of_whether(event):
        event.sim.modify_status().toggle_rain()
        Event(sim, sim.now + 59, "weather")


if __name__ == '__main__':
    sim = Simulation()
    sim.__status__ = Status(sim)
    sim.manager.add_mapping("haul", Aquifer.haul)

    sim.logger.enable(True)

    x = lambda x: x + 1
    y = lambda x: x + 1
    print(x.__code__)

    for i in range(0, 10):
        sim.add_res(Well(sim, Position(0, 10)))
        sim.add_res(Well(sim, Position(0, 20)))
        sim.add_res(Tank(sim, Position(10, 0), 100))
        sim.add_res(Tank(sim, Position(20, 0), 100))
        sim.add_res(Tank(sim, Position(30, 0), 100))
        sim.add_res(Tank(sim, Position(40, 0), 100))
        p = Aquifer(sim, Position(0, 0))
        sim.add_res(p)
        p = Aquifer(sim, Position(0, 0))
        sim.add_res(p)
    sim.run(until=1000)
