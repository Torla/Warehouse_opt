import copy
import csv
import os
import random
import sys
from time import time
from typing import List

import jsonpickle
import math
from simanneal import anneal

import SimMain
import Opt

from SimMain.SimulationParameter import SimulationParameter
from SimMain.main import Test

from SimMain.Monitor import Monitor

import multiprocessing as mp
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from IdeaSim.Simulation import Simulation

from Trace.Trace import TraceParameter


class Opt:
    @staticmethod
    def optimization(opt_par, trace_par, fitness_par, c_par, generations, processes):
        res = []
        t = []
        s = time()
        from Opt.Genetic import opt
        count = 0
        for i in opt(opt_par, trace_par, fitness_par, c_par, 100, 0.2, 0.2, 0, 0.3, 0.1, 0.8, processes):
            count += 1
            if count > generations:
                return OptParameter.map(i.opt_par, i), i.get_average_results()


class OptRange:

    def __init__(self, low, high, decimal=False) -> None:
        self.low = low
        self.high = high
        self.decimal = decimal


class OptParameter(SimulationParameter):

    def __init__(self, Nx, Ny, Nz, Lx, Ly, Lz, Cy, Ax, Vx, Ay, Vy, Az, Vz, Wli, Wsh, Wsa, Cr, Fr, rendiment, Nli,
                 Nsh,
                 Nsa, bay_level, tech, strat, strat_par_x, strat_par_y):
        super().__init__(Nx, Ny, Nz, Lx, Ly, Lz, Cy, Ax, Vx, Ay, Vy, Az, Vz, Wli, Wsh, Wsa, Cr, Fr, rendiment, Nli,
                         Nsh,
                         Nsa, bay_level, tech, strat, strat_par_x, strat_par_y)

    def map(self, solution) -> SimulationParameter:
        assert isinstance(solution, list)
        ret = SimulationParameter(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        i = 0
        for p in self.__dict__:
            if isinstance(self.__dict__[p], OptRange):
                assert 0 <= solution[i] <= 1
                ret.__dict__[p] = solution[i] * (self.__dict__[p].high - self.__dict__[p].low) + self.__dict__[
                    p].low
                if not self.__dict__[p].decimal:
                    ret.__dict__[p] = int(round(ret.__dict__[p], 0))
                i = i + 1
            else:
                ret.__dict__[p] = self.__dict__[p]
        return ret

    def variable_num(self) -> int:
        i = 0
        for p in self.__dict__:
            if isinstance(self.__dict__[p], OptRange):
                i = i + 1
        return i


class FitnessParameter(Monitor.Results):  # todo rewrite this

    def __init__(self, mean_task_wait=0, task_op_time=0, task_tot_time=0, working_time=0, time_per_task=0,
                 energy_consumed=0., area=0, volume=0, num_lifts=0, num_shuttle=0, num_sats=0, single_CT=0,
                 double_CT=0, single_CT_E=0, double_CT_E=0, single_CT_V=0, double_CT_V=0, lifts_proc=0, shut_proc=0,
                 sat_proc=0, lifts_util=0, sat_util=0, shut_util=0, energy_per_task=0, cost=0, completeness=0, Th=0):
        super().__init__()
        self.Ny = 0
        self.Nx = 0
        self.Nz = 0
        self.strat_param = 0
        self.Th = Th
        self.completeness = completeness
        self.mean_task_wait = mean_task_wait
        self.mean_task_op_time = task_op_time
        self.mean_task_tot_time = task_tot_time
        self.working_time = working_time
        self.time_per_task = time_per_task
        self.energy_consumed = energy_consumed
        self.energy_per_task = energy_per_task
        self.area = area
        self.volume = volume
        self.num_lifts = num_lifts
        self.num_shuttles = num_shuttle
        self.num_sats = num_sats
        self.lifts_util_proc = lifts_proc
        self.shut_util_proc = shut_proc
        self.sat_util_proc = sat_proc
        self.lifts_util = lifts_util
        self.shut_util = shut_util
        self.sat_util = sat_util
        self.single_CT = single_CT
        self.double_CT = double_CT
        self.single_CT_V = single_CT_V
        self.double_CT_V = double_CT_V
        self.single_CT_E = single_CT_E
        self.double_CT_E = double_CT_E
        self.cost = cost


class Solution(List):
    p_pool = None

    def __init__(self, opt_par, t_par, fitness_par, c_par, array=None) -> None:
        # assert isinstance(opt_par, OptParameter)
        # assert isinstance(fitness_par, FitnessParameter)
        self.opt_par = opt_par
        self.t_par = t_par
        self.fitness_par = fitness_par
        self.cost_par = c_par
        self.fitness = None
        if array is None:
            super().__init__([])
            for i in range(0, opt_par.variable_num()):
                self.append(random.random())
                # self.append(0.01)
        else:
            super().__init__(array)

        seeds = []
        for seed in self.t_par.seed:
            n = copy.copy(t_par)
            n.seed = seed
            seeds.append(n)
        self.res = Solution.p_pool.starmap_async(Test.test, [(self.opt_par.map(self), t, self.cost_par) for t in seeds])

        self.saved = False

    @staticmethod
    def set_process_pool(n):
        Solution.p_pool = mp.Pool(n)

    def get_fitness(self):
        ret = 0
        try:
            results = self.res.get()
            print("done")
        except Exception as err:
            return np.inf
        i = 0
        for res in results:
            if not self.saved:
                d = self.opt_par.map(self).__dict__
                t = copy.copy(self.t_par)
                t.seed = self.t_par.seed[i]
                i += 1
                d.update(t.__dict__)
                d.update(res.__dict__)
                with open("results.csv", mode="a+", newline='') as f:
                    w = csv.DictWriter(f,
                                       fieldnames=(list(d.keys())))
                    if os.stat(f.name).st_size < 10:
                        w.writeheader()
                    w.writerow(d)
            for p in res.__dict__:
                if isinstance(res.__dict__[p], int) or isinstance(res.__dict__[p], float):
                    ret += (res.__dict__[p] * self.fitness_par.__dict__[p]) / len(results)
                else:
                    ret += 10000000000
        self.saved = True
        return ret

    def get_average_results(self):
        ret = Monitor.Results()
        for p in ret.__dict__:
            ret.__dict__[p] = 0
        try:
            results = self.res.get()
        except Exception as err:
            return np.inf
        i = 0
        for res in results:
            if not self.saved:
                d = self.opt_par.map(self).__dict__
                t = copy.copy(self.t_par)
                t.seed = self.t_par.seed[i]
                i += 1
                d.update(t.__dict__)
                d.update(res.__dict__)
                w = csv.DictWriter(open("results_old.csv", mode="a+"),
                                   fieldnames=(list(d.keys())))
                if os.stat("results_old.csv").st_size < 10:
                    w.writeheader()
                w.writerow(d)
            for p in res.__dict__:
                if isinstance(res.__dict__[p], int) or isinstance(res.__dict__[p], float):
                    ret.__dict__[p] += (res.__dict__[p]) / len(results)
                else:
                    ret.__dict__[p] = 999999999
        self.saved = True
        return ret


if __name__ == '__main__':
    def test():

        for tech in [0, 1, 2]:
            with open("cost_vs_energy_tech{tech}.csv".format(tech=tech), "w") as f:
                f.write("par,cost,energy\n")
            for cost_f in np.arange(0.7, 1.05, 0.05):
                print(str(tech) + " " + str(cost_f))
                par = OptParameter(Nx=OptRange(10, 50), Ny=OptRange(3, 20), Nz=OptRange(10, 50),
                                   Lx=1, Ly=1.5, Lz=1.2, Cy=0,
                                   Ax=0.8, Vx=4, Ay=0.8, Vy=0.9, Az=0.7, Vz=1.20,
                                   # Ax=0.2, Vx=4, Ay=0.2, Vy=0.9, Az=0.2, Vz=1.20,
                                   Wli=1850, Wsh=850, Wsa=350,
                                   Cr=0.02, Fr=1.15, rendiment=0.9,
                                   Nli=OptRange(1, 5), Nsh=OptRange(1, 3), Nsa=OptRange(1, 3),
                                   bay_level=0,
                                   tech=tech, strat=1, strat_par_x=OptRange(0, 10, decimal=True),
                                   strat_par_y=OptRange(0, 1))

                t_par = TraceParameter(sim_time=1000, types=np.repeat(1 / 10, 10), int_mean=25, start_fullness=0.5,
                                       seed=[1])
                f_par = FitnessParameter(completeness=-1000000000, cost=cost_f, energy_consumed=(1 - cost_f)/1000)
                c_par = Monitor.CostParam(intended_time=3.154e+8, lift=20000, shuttle=50000, shuttle_fork=35000,
                                          satellite=35000, transelevator=40000,
                                          scaffolding=30, energy_cost=0.0356 / 1000)
                r1, r2 = Opt.optimization(par, t_par, f_par, c_par, 10000, 2)

                with open("cost_vs_energy_tech{tech}.csv".format(tech=tech), "a+") as f:
                    # f.write(
                    #    "tech " + str(tech) + "  cost_f " + str(cost_f) + ":\n" + str(r1.__dict__) + "\n\n\n\n" + str(
                    #       r2) + "\n\n\n\n\n")
                    f.write(
                        "{par},{cost},{energy}\n".format(par=cost_f, cost=r2.cost, energy=r2.energy_consumed))


    start = time()
    print("start")
    test()
    print("\n\n")
    print(time() - start)
