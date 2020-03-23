from simpy import Container

from IdeaSim import Simulation, Event

# todo add mapping
from IdeaSim import Actions


class Manager:
    class RetryLater(Exception):

        def __init__(self, *args: object) -> None:
            super().__init__(*args)

    def __init__(self, simulation):
        assert isinstance(simulation, Simulation.Simulation)
        self.sim = simulation
        self.type_map = {}
        self.event_queue = []
        self.sim.process(self.__auto_run__())
        self.activation = Container(self.sim, float('inf'), 0)
        self.last_active = -1

    def add_mapping(self, event_type, func):
        self.type_map[event_type] = func

    def activate(self):
        def a():
            yield self.activation.put(1)

        self.sim.process(a())

    def manage(self, event):
        assert isinstance(event, Event.Event)
        ret = None
        try:
            ret = self.type_map[event.event_type](event)
        except Manager.RetryLater:
            self.event_queue.append(event)
        if isinstance(ret, Actions.ActionsGraph):
            Actions.Executor(self.sim, ret)

    def __auto_run__(self):
        while True:
            yield self.activation.get(1)
            if self.activation.level != 0:
                yield self.activation.get(self.activation.level)
            if self.last_active == self.sim.now:
                yield self.sim.wait(1)
            self.last_active = self.sim.now
            events = self.event_queue[:]
            self.event_queue = []
            for event in events:
                assert isinstance(event, Event.Event)
                self.manage(event)
