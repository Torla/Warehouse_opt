import copy
import csv
import os
import random
import time

import jsonpickle
import pandas as pd
from math import floor, sqrt, ceil
import numpy as np

from IdeaSim.Simulation import Simulation
from SimMain.Monitor import Monitor
from SimMain.SimulationParameter import SimulationParameter
from Trace.Trace import trace_generator, TraceParameter
from SimMain.Warehouse import Warehouse
from matplotlib import pyplot as plt
import multiprocessing as mp


class Test:
    @staticmethod
    def test(parameter, trace_parameter, cost_par=None, log=False):
        class Status:
            def __init__(self, parameter, monitor):
                self.parameter = parameter
                self.monitor = monitor

        # todo temporari
        # parameter.Nx = round(4000 / (parameter.Nz * parameter.Ny))
        # print("\n\n")
        # print(parameter.Nx)
        # print(parameter.Ny)
        # print(parameter.Nz)
        # print("\n\n")
        sim = Simulation(Status(parameter, None))
        sim.__status__.monitor = Monitor(sim)
        sim.logger.enable(log)
        # env = simpy.RealtimeEnvironment(0, 0.1, False)
        # warehouse = Warehouse(env, parameter, trace_load("trace1.json"))
        warehouse = Warehouse(sim, parameter, trace_parameter)
        sim.run(until=trace_parameter.sim_time)

        ret = sim.get_status().monitor.get_result(cost_param=cost_par)

        return ret


# warehouse.monitor.plot(definition=3600)
# return warehouse.monitor.get_result()


if __name__ == '__main__':
    def graphs():

        for tech in range(0, 3):
            for xpar in [0.01]:
                par = SimulationParameter(Nx=50, Ny=10, Nz=50,
                                          Lx=1, Ly=1.5, Lz=1.2, Cy=0,
                                          Ax=0.8, Vx=4, Ay=0.8, Vy=0.9, Az=0.7, Vz=1.20,
                                          Wli=1850, Wsh=850, Wsa=350,
                                          Cr=0.02, Fr=1.15, rendiment=0.9,
                                          Nli=3, Nsh=3, Nsa=2,
                                          bay_level=0,
                                          tech=tech, strat=1, strat_par_x=xpar, strat_par_y=1)
                t_par = TraceParameter(sim_time=3600 * 6, types={"Type" + str(i): (i / 10) for i in np.repeat(1, 10)},
                                       int_mean=25,
                                       start_fullness=0.5,
                                       seed=[1])
                c_par = Monitor.CostParam(intended_time=3.154e+8, lift=20000, shuttle=50000, shuttle_fork=35000,
                                          satellite=35000, transelevator=40000,
                                          scaffolding=30, energy_cost=0.0356 / 1000)

                res = Test.test(parameter=par, trace_parameter=t_par, cost_par=c_par, log=True)
                d = par.__dict__
                t = copy.copy(t_par)
                t.seed = t_par.seed[0]
                d.update(t.__dict__)
                d.update(res.__dict__)
                with open("../data/strategy_par_x.csv", mode="a+", newline='') as f:
                    w = csv.DictWriter(f,
                                       fieldnames=(list(d.keys())))
                    if os.stat(f.name).st_size < 10:
                        w.writeheader()
                    w.writerow(d)


    def test():
        area = 8 * 100
        nz = 200
        par = SimulationParameter(Nx=15, Ny=5, Nz=200,
                                  Lx=5, Ly=5, Lz=5, Cy=0,
                                  Ax=0.8, Vx=4, Ay=0.8, Vy=0.9, Az=0.7, Vz=1.20,
                                  Wli=1850, Wsh=850, Wsa=350,
                                  Cr=0.02, Fr=1.15, rendiment=0.9,
                                  Nli=34, Nsh=4, Nsa=4,
                                  bay_level=0,
                                  tech=0, strat=1, strat_par_x=1, strat_par_y=1)
        t_par = TraceParameter(sim_time=360 * 3, types={"Type" + str(i): (1 / 10) for i in range(0, 10)}, int_mean=25,
                               start_fullness=0.5,
                               seed=1023)
        c_par = Monitor.CostParam(intended_time=3.154e+8, lift=20000, shuttle=50000, shuttle_fork=35000,
                                  satellite=35000, transelevator=40000,
                                  scaffolding=30, energy_cost=0.0356 / 1000)
        res = Test.test(parameter=par, trace_parameter=t_par, cost_par=c_par, log=True)
        print(res)


    def only_plot():
        if __name__ == '__main__':

            with open("../resultsLowNz.json", "r") as f:
                result = jsonpickle.loads(f.read())

            c = "rgbyk"
            for p in Monitor.Results().__dict__:
                for i in range(0, len(result)):
                    lists = sorted(result[i].items(), key=lambda x: int(x[0]))
                    x, y = zip(*lists)  # unpack a l
                    # ist of pairs into two tuples
                    y = [a.__dict__[p] for a in y]
                    plt.plot(x, y, c[i], label="tech" + str(i))
                plt.ylabel(p)
                plt.xlabel('Nz')
                plt.legend()
                plt.savefig("../output/lowNz/" + str(p) + ".png", bbox_inches='tight')
                plt.close()


    def adjacency():
        d = {k.strip(): {row['antecedents'].strip(): row["lift"] for i, row in v.iterrows()} for k, v in
             pd.read_csv("ad_rule.csv").groupby(by="consequents")}
        gen = pd.read_csv("Original_dataset.csv", encoding='unicode_escape').dropna()
        gen["Description"] = gen["Description"].map(lambda x: x.strip())
        gen = gen.groupby("Description",
                          as_index=False).count().rename(
            {"Country": "count"}, axis=1)[["Description", "count"]]
        gen = {row["Description"].strip(): row["count"] / gen["count"].sum() for index, row in gen.iterrows()}
        par = SimulationParameter(Nx=100, Ny=20, Nz=100,
                                  Lx=5, Ly=5, Lz=5, Cy=0,
                                  Ax=0.8, Vx=4, Ay=0.8, Vy=0.9, Az=0.7, Vz=1.20,
                                  Wli=1850, Wsh=850, Wsa=350,
                                  Cr=0.02, Fr=1.15, rendiment=0.9,
                                  Nli=4, Nsh=4, Nsa=4,
                                  bay_level=0,
                                  tech=2, strat=2, strat_par_x=1, strat_par_y=100, adjacency=d)
        t_par = TraceParameter(sim_time=36000, types=gen, int_mean=402, start_fullness=0.7,
                               seed=1023)
        c_par = Monitor.CostParam(intended_time=3.154e+8, lift=20000, shuttle=50000, shuttle_fork=35000,
                                  satellite=35000, transelevator=40000,
                                  scaffolding=30, energy_cost=0.0356 / 1000)
        res = Test.test(parameter=par, trace_parameter=t_par, cost_par=c_par, log=True)
        print(res)


    start_time = time.time()
    adjacency()
    print(time.time() - start_time)
