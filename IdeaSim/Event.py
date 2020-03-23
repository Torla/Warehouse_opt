# to be implemented by the and user
from IdeaSim import Simulation


class Event:
    def __init__(self, sim, time, event_type, param=None):
        assert isinstance(sim, Simulation.Simulation)
        self.sim = sim
        self.time = time
        self.event_type = event_type
        self.param = param
        if self.time is not None:
            self.sim.process(self.__dispatch__())

    def __dispatch__(self):
        yield self.sim.wait(self.time - self.sim.now)
        self.sim.manager.manage(self)

    def launch(self):
        self.sim.manager.manage(self)

    def __str__(self) -> str:
        return str(self.event_type)
