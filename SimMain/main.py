import random
import time

from math import floor
import numpy as np

from IdeaSim.Simulation import Simulation
from SimMain.Monitor import Monitor
from SimMain.SimulationParameter import SimulationParameter
from Trace.Trace import trace_generator, TraceParameter
from SimMain.Warehouse import Warehouse
from matplotlib import pyplot as plt


class Test:
    @staticmethod
    def test(parameter, trace_parameter, log=False):
        class Status:
            def __init__(self, parameter, monitor):
                self.parameter = parameter
                self.monitor = monitor

        sim = Simulation(Status(parameter, None))
        sim.__status__.monitor = Monitor(sim)
        sim.logger.enable(log)
        # env = simpy.RealtimeEnvironment(0, 0.1, False)
        # warehouse = Warehouse(env, parameter, trace_load("trace1.json"))
        warehouse = Warehouse(sim, parameter, trace_parameter)
        sim.run()

        sim.logger.log(str(sim.get_status().monitor.get_result()))
        return sim.get_status().monitor.get_result()


# warehouse.monitor.plot(definition=3600)
# return warehouse.monitor.get_result()


if __name__ == '__main__':
    def graphs():
        area = 8 * 100
        nz = 300
        result = []
        for tech in range(0, 3):
            result.append({})
            for par_x in range(0, 101, 5):
                par = SimulationParameter(Nx=floor(area / nz), Ny=10, Nz=nz,
                                          Lx=5, Ly=5, Lz=5, Cy=0,
                                          Ax=0.8, Vx=4, Ay=0.8, Vy=0.9, Az=0.7, Vz=1.20,
                                          Wli=1850, Wsh=850, Wsa=350,
                                          Cr=0.02, Fr=1.15, rendiment=0.9,
                                          Nli=2, Nsh=4, Nsa=4,
                                          bay_level=1.5,
                                          tech=tech, strat=1, strat_par_x=par_x / 100, strat_par_y=1 - par_x / 100)
                t_par = TraceParameter(sim_time=86400, types=[0.4, 0.3, 0.3], int_mean=100, start_fullness=0,
                                       seed=1023)
                res = []
                res.append(Test.test(parameter=par, trace_parameter=t_par, log=False))
                t_par.seed = 1234
                res.append(Test.test(parameter=par, trace_parameter=t_par, log=False))
                t_par.seed = 12
                res.append(Test.test(parameter=par, trace_parameter=t_par, log=False))
                result[tech][par_x / 100] = 3600 / np.average([i.mean_task_op_time for i in res])
                print(str(tech) + " " + str(par_x / 100) + " " + str(result[tech][par_x / 100]))

        fig = plt.figure()

        lists = sorted(result[0].items())
        x, y = zip(*lists)  # unpack a list of pairs into two tuples
        plt.plot(x, y, "r", label="tech0")
        lists = sorted(result[1].items())
        x, y = zip(*lists)  # unpack a list of pairs into two tuples
        plt.plot(x, y, "y", label="tech1")
        lists = sorted(result[2].items())
        x, y = zip(*lists)  # unpack a list of pairs into two tuples
        plt.plot(x, y, "b", label="tech2")
        plt.ylabel('Th')
        plt.xlabel('strat_par_x')
        plt.legend()

        plt.show()


    def test():
        area = 8 * 100
        nz = 200
        par = SimulationParameter(Nx=floor(area / nz), Ny=10, Nz=nz,
                                  Lx=5, Ly=5, Lz=5, Cy=0,
                                  Ax=0.8, Vx=4, Ay=0.8, Vy=0.9, Az=0.7, Vz=1.20,
                                  Wli=1850, Wsh=850, Wsa=350,
                                  Cr=0.02, Fr=1.15, rendiment=0.9,
                                  Nli=2, Nsh=4, Nsa=4,
                                  bay_level=1.5,
                                  tech=0, strat=1, strat_par_x=1, strat_par_y=1)
        t_par = TraceParameter(sim_time=86400, types=[0.4, 0.3, 0.3], int_mean=50, start_fullness=0.9,
                               seed=1023)
        res = Test.test(parameter=par, trace_parameter=t_par, log=True)
        print(res)


    graphs()
    # test()
