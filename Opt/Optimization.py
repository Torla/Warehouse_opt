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
    def optimization(opt_par, trace_par, fitness_par, generations, processes):
        res = []
        t = []
        s = time()
        from Opt.Genetic import opt
        count = 0
        for i in opt(opt_par, trace_par, fitness_par, 50, 0.2, 1, -0.1, 0.3, 0, 0.5, processes):
            # print("\n\nt: " + str(time() - s))
            # i.get_fitness()
            # print("fit: " + str(i.get_fitness()))
            # print(str(i.get_average_results()))
            # res.append(i.get_fitness())
            print(count)
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


class FitnessParameter(Monitor.Results):

    def __init__(self, mean_task_wait=0, task_op_time=0, task_tot_time=0, working_time=0, time_per_task=0,
                 energy_consumed=0., area=0, volume=0, num_lifts=0, num_shuttle=0, num_sats=0, single_CT=0,
                 double_CT=0, single_CT_E=0, double_CT_E=0, single_CT_V=0, double_CT_V=0, lifts_proc=0, shut_proc=0,
                 sat_proc=0, lifts_util=0, sat_util=0, shut_util=0, energy_per_task=0):
        super().__init__()
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


class Solution(List):
    p_pool = None

    def __init__(self, opt_par, t_par, fitness_par, array=None) -> None:
        # assert isinstance(opt_par, OptParameter)
        # assert isinstance(fitness_par, FitnessParameter)
        self.opt_par = opt_par
        self.t_par = t_par
        self.fitness_par = fitness_par
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
                w = csv.DictWriter(open("results.csv", mode="a+"),
                                   fieldnames=(list(d.keys())))
                if os.stat("results.csv").st_size < 10:
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
        par = OptParameter(Nx=10, Ny=10, Nz=100,
                           Lx=1, Ly=1.5, Lz=1.2, Cy=0,
                           Ax=OptRange(0.1, 1.5), Vx=OptRange(0.1, 5.5), Ay=OptRange(0.1, 1.5), Vy=OptRange(0.1, 1.5),
                           Az=OptRange(0.1, 1.5),
                           Vz=OptRange(0, 2.5),
                           Wli=1850, Wsh=850, Wsa=350,
                           Cr=0.02, Fr=1.15, rendiment=0.9,
                           Nli=OptRange(1, 5), Nsh=OptRange(1, 5), Nsa=OptRange(1, 5),
                           # todo collega questi con le dimensioni Nz/2 Nx Ny
                           bay_level=0,
                           tech=1, strat=1, strat_par_x=OptRange(0, 1, decimal=True),
                           strat_par_y=OptRange(0, 1, decimal=True))

        t_par = TraceParameter(sim_time=6000, types=np.repeat(0.1, 10), int_mean=200, start_fullness=0.4,
                               # todo 0.40 0.60 0.80
                               seed=[100, 200, 300])
        f_par = FitnessParameter(num_lifts=10, num_sats=1, num_shuttle=1)
        str(Opt.optimization(par, t_par, f_par, 10, 3))


    def graphs():
        result = []
        area = 800
        for tech in range(0, 3):
            result.append({})
            for nz in range(20, 201, 30):
                lifts = OptRange(1, 10) if tech == 2 else OptRange(math.ceil(nz / 6), math.ceil(nz / 6) + 10)
                start = time()
                par = OptParameter(Nx=1, Ny=OptRange(2, 10), Nz=nz,
                                   Lx=1, Ly=1.5, Lz=1.2, Cy=0,
                                   Ax=0.8, Vx=4, Ay=0.8, Vy=0.9, Az=0.7, Vz=1.20,
                                   Wli=1850, Wsh=850, Wsa=350,
                                   Cr=0.02, Fr=1.15, rendiment=0.9,
                                   Nli=lifts, Nsh=OptRange(1, 10), Nsa=OptRange(1, 10),
                                   bay_level=0,
                                   tech=tech, strat=1, strat_par_x=OptRange(0, 1, decimal=True),
                                   strat_par_y=OptRange(0, 1, decimal=True))

                t_par = TraceParameter(sim_time=3600 * 3, types=[0.4, 0.3, 0.3], int_mean=25, start_fullness=0.5,
                                       seed=[100, 200, 300])
                f_par = FitnessParameter(task_tot_time=100, num_lifts=10, num_sats=1, num_shuttle=1)
                par, res = Opt.optimization(par, t_par, f_par, 10, int(sys.argv[1]))
                result[tech][nz] = res
                print(str(tech) + " " + str(nz) + " :\n" + str(result[tech][nz]))
                print("time: " + str(time() - start))
                print("\n")

        with open("results.json", "w") as f:
            f.write(jsonpickle.encode(result))
        with open("results.json", "r") as f:
            result = jsonpickle.loads(f.read())

        c = "rgbyk"
        for p in res.__dict__:
            for i in range(0, len(result)):
                lists = sorted(result[i].items(), key=lambda x: int(x[0]))
                x, y = zip(*lists)  # unpack a l
                # ist of pairs into two tuples
                y = [a.__dict__[p] for a in y]
                plt.plot(x, y, c[i], label="tech" + str(i))
            plt.ylabel(p)
            plt.xlabel('Nz')
            plt.legend()
            plt.savefig("output/" + str(p) + ".png", bbox_inches='tight')
            plt.close()


    start = time()
    print("start")
    graphs()
    print("\n\n")
    print(time() - start)
