import math

import SimMain.Strategy
from IdeaSim.Simulation import Simulation
from Resources import Bay
from Resources.Channel import Channel
from Resources.Lift import Lift
from Resources.Movement import Position
from Resources.Satellite import Satellite
from Resources.Shuttle import Shuttle
from SimMain.SimulationParameter import SimulationParameter
from Task.TaskDipatcher import TaskDispatcher


class Warehouse:
    def __init__(self, sim, parameter, trace):
        assert isinstance(parameter, SimulationParameter)
        self.parameter = parameter
        assert (isinstance(sim, Simulation))
        self.sim = sim
        # available res
        #        self.resources = Resources(sim)
        # all res
        self.all_resources = []
        self.sim.manager.add_mapping("new_task", SimMain.Strategy.Strategy.strategy)
        TaskDispatcher(sim, trace)

        lifts = []
        shuttles = []
        satellites = []
        channels = []
        bay = Bay.Bay(self.sim,Position(None, self.parameter.bay_level, 0, 0))
        for i in range(0, self.parameter.Nli):
            lifts.append(Lift(self.sim, Position(i, 0, 0, 0), self.parameter.Ay, self.parameter.Vy, self.parameter))
            for j in range(0, self.parameter.Nsh):
                shuttles.append(
                    Shuttle(self.sim, Position(i, j, 0, 0), self.parameter.Ax, self.parameter.Vx, self.parameter))
                for l in range(0, self.parameter.Nsa):
                    satellites.append(
                        Satellite(self.sim, Position(i, j, 0, 0), self.parameter.Az, self.parameter.Vz, self.parameter))

        for i in range(0, self.parameter.Nli):
            for y in range(0, self.parameter.Ny):
                for x in range(0, self.parameter.Nx):
                    # division of Nz between sections
                    nz_of_section = math.floor(self.parameter.Nz / self.parameter.Nli)
                    if i == self.parameter.Nli - 1:
                        nz_of_section += self.parameter.Nz % self.parameter.Nli
                    # right and left channel
                    channels.append(
                        Channel(self.sim, math.floor((nz_of_section / 2)), lifts[i],
                                Position(i, y, x, 0),
                                Channel.Orientations.LEFT,
                                ))
                    channels.append(
                        Channel(self.sim, math.ceil((nz_of_section / 2) / self.parameter.Nli), lifts[i],
                                Position(i, y, x, 0),
                                Channel.Orientations.RIGHT,
                                ))
        self.sim.add_res(bay)
        for r in lifts:
            self.sim.add_res(r)
        for r in shuttles:
            self.sim.add_res(r)
        for r in satellites:
            self.sim.add_res(r)
        for r in channels:
            self.sim.add_res(r)


        # self.monitor = Monitor(env, self.task_queue, self.parameter, self)