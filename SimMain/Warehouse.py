from random import randint

import math
import numpy as np

from SimMain.Strategy import Strategy
from IdeaSim.Simulation import Simulation
from Resources import Bay
from Resources.Channel import Channel
from Resources.Lift import Lift
from Resources.Movement import Position
from Resources.Satellite import Satellite
from Resources.Shuttle import Shuttle
from SimMain.SimulationParameter import SimulationParameter
from Task.Item import Item
from Task.Task import Task, OrderType
from Task.TaskDispatcher import TaskDispatcher
from Trace.Trace import trace_generator, TraceParameter


class Warehouse:
    def __init__(self, sim, parameter, trace_parameter):
        assert isinstance(parameter, SimulationParameter)
        self.parameter = parameter
        assert (isinstance(sim, Simulation))
        assert (isinstance(trace_parameter, TraceParameter))
        trace = trace_generator(trace_parameter)
        self.sim = sim
        # available res
        #        self.resources = Resources(sim)
        # all res
        self.all_resources = []
        self.sim.manager.add_mapping("new_task", Strategy.strategy)
        TaskDispatcher(sim, trace)

        lifts = []
        shuttles = []
        satellites = []
        channels = []
        bay = Bay.Bay(self.sim, Position(None, self.parameter.bay_level, 0, 0))
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
                        Channel(self.sim, math.ceil((nz_of_section / 2)), lifts[i],
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

        if trace_parameter.start_fullness < 1:
            item_to_add = math.floor(parameter.Nz * parameter.Nx * parameter.Ny * trace_parameter.start_fullness)
        else:
            item_to_add = trace_parameter.start_fullness
        i = 0

        if parameter.strategy == 1:
            def w_dist(x, y, par):
                assert isinstance(par, SimulationParameter)
                return abs(x.level - y.level) * par.strategy_par_y * par.Ly + abs(
                    x.x - y.x) * par.strategy_par_x * par.Lx

            channels = sorted(self.sim.find_res(lambda x: isinstance(x, Channel), free=False),
                              key=lambda x: w_dist(x.position, bay.position, parameter))
            while i < item_to_add:
                task = Task(Item(np.random.choice(a=[i for i in trace_parameter.types.keys()],
                                                  p=[i for i in trace_parameter.types.values()])),
                            OrderType.DEPOSIT)
                Strategy.bay = None
                Strategy.strategy1_static = None
                channel = channels.pop(0)
                channel.items.extend([Item(task.item.item_type) for i in range(0, channel.capacity)])
                i += channel.capacity

        else:
            while i < item_to_add:
                task = Task(Item(
                    np.random.choice(a=[i for i in trace_parameter.types.keys()], p=[i for i in trace_parameter.types.values()])),
                            OrderType.DEPOSIT)
                Strategy.bay = None
                Strategy.strategy1_static = None
                selection = Strategy.__dict__["strategy" + str(parameter.strategy)] \
                    .__func__(task, sim, parameter)
                assert isinstance(selection, int)
                channel = sim.find_res_by_id(selection, False)
                channel.items.extend([Item(task.item.item_type) for i in range(0, channel.capacity)])
                i += channel.capacity
