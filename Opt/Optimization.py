import copy
import csv
import os
import random
from time import time
from typing import List
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
    def optimization():
        par = OptParameter(Nx=OptRange(5, 10), Ny=OptRange(5, 10), Nz=OptRange(100, 200),
                           Lx=5, Ly=5, Lz=5, Cy=1,
                           Ax=0.8, Vx=4, Ay=0.8, Vy=0.9, Az=0.7, Vz=1.20,
                           Wli=1850, Wsh=850, Wsa=350,
                           Cr=0.02, Fr=1.15, rendiment=0.9,
                           Nli=OptRange(5, 10), Nsh=OptRange(1, 4), Nsa=OptRange(1, 4),
                           bay_level=OptRange(0, 5, True),
                           tech=OptRange(0, 2), strat=1, strat_par_x=OptRange(0, 1, True),
                           strat_par_y=OptRange(0, 1, True))

        t_par = TraceParameter(sim_time=10000, type_num=2, int_mean=100, num_mean=25, mean_present=50, seed=[35, 64])
        f_par = FitnessParameter(time_per_task=1, area=0.1)

        for m in [0.2]:
            for pop in [10]:
                res = []
                t = []
                s = time()
                from Opt.Genetic import opt
                for i in opt(par, t_par, f_par, pop, 0.2, m, 0.1, 0.5, 4):
                    print("t: " + str(time() - s))
                    print(i.get_fitness())
                    print(par.map(i).__dict__)
                    print(str(i.res.get()[0]))
                    t.append(time() - s)
                    res.append(i.get_fitness())
                    if time() - s > 1000:
                        break
                print(str(pop) + "/" + str(m))
                # open("runs/big" + str(pop) + "m" + str(round(m * 100)) + ".csv", mode="w+", ).write(
                #    pd.Series(res, index=t).to_csv(header=False))


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


class FitnessParameter(Monitor.Results):

    def __init__(self, mean_task_wait=0, task_op_time=0, task_tot_time=0, working_time=0, time_per_task=0,
                 energy_consumed=0., area=0, volume=0):
        super().__init__()
        self.mean_task_wait = mean_task_wait
        self.mean_task_op_time = task_op_time
        self.mean_task_tot_time = task_tot_time
        self.working_time = working_time
        self.time_per_task = time_per_task
        self.energy_consumed = energy_consumed
        self.area = area
        self.volume = volume


class Solution(List):
    p_pool = None

    def __init__(self, opt_par, t_par, fitness_par, array=None) -> None:
        #        assert isinstance(opt_par, OptParameter)
        #        assert isinstance(fitness_par, FitnessParameter)
        self.opt_par = opt_par
        self.t_par = t_par
        self.fitness_par = fitness_par
        self.fitness = None
        if array is None:
            super().__init__([])
            for i in range(0, opt_par.variable_num()):
                self.append(random.random())
        else:
            super().__init__(array)

        seeds = []
        for seed in self.t_par.seed:
            n = copy.copy(t_par)
            n.seed = seed
            seeds.append(n)
        self.res = Solution.p_pool.starmap_async(Test.test, [(self.opt_par.map(self), t) for t in seeds])

        self.saved = False

    @staticmethod
    def set_process_pool(n):
        Solution.p_pool = mp.Pool(n)

    def get_fitness(self):
        ret = 0
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
                w = csv.DictWriter(open("results.csv", mode="a+"),
                                   fieldnames=(list(d.keys())))
                if os.stat("results.csv").st_size < 10:
                    w.writeheader()
                w.writerow(d)
            for p in res.__dict__:
                ret += (res.__dict__[p] * self.fitness_par.__dict__[p]) / len(results)
        self.saved = True
        return ret


if __name__ == '__main__':
    Opt.optimization()
