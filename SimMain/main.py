import random
import time

from math import floor, sqrt
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
        sim.run(until=trace_parameter.sim_time)

        sim.logger.log(str(sim.get_status().monitor.get_result()))
        return sim.get_status().monitor.get_result()


# warehouse.monitor.plot(definition=3600)
# return warehouse.monitor.get_result()


if __name__ == '__main__':
    def graphs():
        result = []
        result1 = []
        result2 = []
        for nsh in range(1, 4):
            result.append({})
            result1.append({})
            result2.append({})
            for nsa in range(1, 5, 1):
                par = SimulationParameter(Nx=15, Ny=5, Nz=100,
                                          Lx=5, Ly=5, Lz=5, Cy=0,
                                          Ax=0.8, Vx=4, Ay=0.8, Vy=0.9, Az=0.7, Vz=1.20,
                                          Wli=1850, Wsh=850, Wsa=350,
                                          Cr=0.02, Fr=1.15, rendiment=0.9,
                                          Nli=2, Nsh=nsh, Nsa=nsa,
                                          bay_level=1.5,
                                          tech=2, strat=1, strat_par_x=1, strat_par_y=1)
                t_par = TraceParameter(sim_time=86400, types=[0.4, 0.3, 0.3], int_mean=25, start_fullness=0.5,
                                       seed=1023)
                res = []
                res.append(Test.test(parameter=par, trace_parameter=t_par, log=False))
                t_par.seed = 1234
                res.append(Test.test(parameter=par, trace_parameter=t_par, log=False))
                t_par.seed = 12
                res.append(Test.test(parameter=par, trace_parameter=t_par, log=False))
                result[nsh - 1][nsa] = np.average([i.lifts_util for i in res])
                result1[nsh - 1][nsa] = np.average([i.shut_util for i in res])
                result2[nsh - 1][nsa] = np.average([i.sat_util for i in res])
                print(str(nsh) + " " + str(nsa) + " " + str(result[nsh - 1][nsa]))
                print(str(nsh) + " " + str(nsa) + " " + str(result1[nsh - 1][nsa]))
                print(str(nsh) + " " + str(nsa) + " " + str(result2[nsh - 1][nsa]))
                print("\n")


        c = "rgbyk"
        for i in range(0, len(result)):
            lists = sorted(result[i].items())
            x, y = zip(*lists)  # unpack a list of pairs into two tuples
            plt.plot(x, y, c[i], label=str(i + 1) + " nsh")
        # lists = sorted(result[1].items())
        # x, y = zip(*lists)  # unpack a list of pairs into two tuples
        # plt.plot(x, y, "y", label="tech1")
        # lists = sorted(result[2].items())
        # x, y = zip(*lists)  # unpack a list of pairs into two tuples
        # plt.plot(x, y, "b", label="tech2")
        plt.ylabel('Lift util')
        plt.xlabel('Nsa')
        plt.legend()

        plt.show()

        for i in range(0, len(result1)):
            lists = sorted(result1[i].items())
            x, y = zip(*lists)  # unpack a list of pairs into two tuples
            plt.plot(x, y, c[i], label=str(i + 1) + " nsh")
            # lists = sorted(result[1].items())
            # x, y = zip(*lists)  # unpack a list of pairs into two tuples
            # plt.plot(x, y, "y", label="tech1")
            # lists = sorted(result[2].items())
            # x, y = zip(*lists)  # unpack a list of pairs into two tuples
            # plt.plot(x, y, "b", label="tech2")
        plt.ylabel('Shutlle util')
        plt.xlabel('Nsa')
        plt.legend()

        plt.show()

        for i in range(0, len(result2)):
            lists = sorted(result2[i].items())
            x, y = zip(*lists)  # unpack a list of pairs into two tuples
            plt.plot(x, y, c[i], label=str(i + 1) + " nsh")
            # lists = sorted(result[1].items())
            # x, y = zip(*lists)  # unpack a list of pairs into two tuples
            # plt.plot(x, y, "y", label="tech1")
            # lists = sorted(result[2].items())
            # x, y = zip(*lists)  # unpack a list of pairs into two tuples
            # plt.plot(x, y, "b", label="tech2")
        plt.ylabel('Sat util')
        plt.xlabel('Nsa')
        plt.legend()

        plt.show()


    def test():
        area = 8 * 100
        nz = 200
        par = SimulationParameter(Nx=15, Ny=5, Nz=200,
                                  Lx=5, Ly=5, Lz=5, Cy=0,
                                  Ax=0.8, Vx=4, Ay=0.8, Vy=0.9, Az=0.7, Vz=1.20,
                                  Wli=1850, Wsh=850, Wsa=350,
                                  Cr=0.02, Fr=1.15, rendiment=0.9,
                                  Nli=2, Nsh=4, Nsa=4,
                                  bay_level=1.5,
                                  tech=2, strat=1, strat_par_x=1, strat_par_y=1)
        t_par = TraceParameter(sim_time=10000, types=[0.4, 0.3, 0.3], int_mean=10, start_fullness=0.9,
                               seed=1023)
        res = Test.test(parameter=par, trace_parameter=t_par, log=True)
        print(res)


    start_time = time.time()
    test()
    print(time.time() - start_time)
    # test()
