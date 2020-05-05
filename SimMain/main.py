import copy
import random
import time

import jsonpickle
from math import floor, sqrt
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
    def test(parameter, trace_parameter, log=False):
        class Status:
            def __init__(self, parameter, monitor):
                self.parameter = parameter
                self.monitor = monitor

        # todo temporari
        parameter.Nx = round(4000 / (parameter.Nz * parameter.Ny))
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

        ret = sim.get_status().monitor.get_result()

        return ret


# warehouse.monitor.plot(definition=3600)
# return warehouse.monitor.get_result()


if __name__ == '__main__':
    def graphs():
        p_pool = mp.Pool(3)
        result = []
        result1 = []
        result2 = []
        result3 = []
        result4 = []
        result5 = []
        result6 = []
        area = 800
        for tech in range(0, 3):
            result.append({})
            result1.append({})
            result2.append({})
            result3.append({})
            result4.append({})
            result5.append({})
            result6.append({})
            for nz in range(30, 200, 30):
                par = SimulationParameter(Nx=floor(area / nz), Ny=10, Nz=nz,
                                          Lx=1, Ly=1.5, Lz=1.2, Cy=0,
                                          Ax=0.8, Vx=4, Ay=0.8, Vy=0.9, Az=0.7, Vz=1.20,
                                          Wli=1850, Wsh=850, Wsa=350,
                                          Cr=0.02, Fr=1.15, rendiment=0.9,
                                          Nli=1, Nsh=4, Nsa=20,
                                          bay_level=1.5,
                                          tech=tech, strat=1, strat_par_x=1, strat_par_y=1)
                t_par = TraceParameter(sim_time=2500, types=[0.4, 0.3, 0.3], int_mean=25, start_fullness=0,
                                       seed=[1, 2, 3])
                res = []
                seeds = []
                for seed in t_par.seed:
                    n = copy.copy(t_par)
                    n.seed = seed
                    seeds.append(n)
                res = p_pool.starmap_async(Test.test, [(par, t) for t in seeds]).get()
                result[tech][nz] = 3600 / np.average([i.mean_task_tot_time for i in res])
                result1[tech][nz] = np.average([i.single_CT for i in res])
                result2[tech][nz] = np.average([i.double_CT for i in res])
                result3[tech][nz] = np.average([i.energy_per_task for i in res])
                result4[tech][nz] = np.average([i.lifts_util for i in res])
                result5[tech][nz] = np.average([i.shut_util for i in res])
                result6[tech][nz] = np.average([i.sat_util for i in res])
                print(str(tech) + " " + str(nz) + " " + str(result[tech][nz]))
                print(str(tech) + " " + str(nz) + " " + str(result1[tech][nz]))
                print(str(tech) + " " + str(nz) + " " + str(result2[tech][nz]))
                print(str(tech) + " " + str(nz) + " " + str(result3[tech][nz]))
                print(str(tech) + " " + str(nz) + " " + str(result4[tech][nz]))
                print(str(tech) + " " + str(nz) + " " + str(result5[tech][nz]))
                print(str(tech) + " " + str(nz) + " " + str(result6[tech][nz]))
                print("\n")

        c = "rgbyk"
        for i in range(0, len(result)):
            lists = sorted(result[i].items())
            x, y = zip(*lists)  # unpack a list of pairs into two tuples
            plt.plot(x, y, c[i], label="tech" + str(i))
        # lists = sorted(result[1].items())
        # x, y = zip(*lists)  # unpack a list of pairs into two tuples
        # plt.plot(x, y, "y", label="tech1")
        # lists = sorted(result[2].items())
        # x, y = zip(*lists)  # unpack a list of pairs into two tuples
        # plt.plot(x, y, "b", label="tech2")
        plt.ylabel('Th')
        plt.xlabel('Nz')
        plt.legend()

        plt.show()

        for i in range(0, len(result1)):
            lists = sorted(result1[i].items())
            x, y = zip(*lists)  # unpack a list of pairs into two tuples
            plt.plot(x, y, c[i], label="tech" + str(i))
            # lists = sorted(result[1].items())
            # x, y = zip(*lists)  # unpack a list of pairs into two tuples
            # plt.plot(x, y, "y", label="tech1")
            # lists = sorted(result[2].items())
            # x, y = zip(*lists)  # unpack a list of pairs into two tuples
            # plt.plot(x, y, "b", label="tech2")
        plt.ylabel('Single_CT')
        plt.xlabel('Nz')
        plt.legend()

        plt.show()

        for i in range(0, len(result2)):
            lists = sorted(result2[i].items())
            x, y = zip(*lists)  # unpack a list of pairs into two tuples
            plt.plot(x, y, c[i], label="tech" + str(i))
            # lists = sorted(result[1].items())
            # x, y = zip(*lists)  # unpack a list of pairs into two tuples
            # plt.plot(x, y, "y", label="tech1")
            # lists = sorted(result[2].items())
            # x, y = zip(*lists)  # unpack a list of pairs into two tuples
            # plt.plot(x, y, "b", label="tech2")
        plt.ylabel('Duoble_CT')
        plt.xlabel('Nz')
        plt.legend()

        plt.show()

        for i in range(0, len(result3)):
            lists = sorted(result3[i].items())
            x, y = zip(*lists)  # unpack a list of pairs into two tuples
            plt.plot(x, y, c[i], label="tech" + str(i))
            # lists = sorted(result[1].items())
            # x, y = zip(*lists)  # unpack a list of pairs into two tuples
            # plt.plot(x, y, "y", label="tech1")
            # lists = sorted(result[2].items())
            # x, y = zip(*lists)  # unpack a list of pairs into two tuples
            # plt.plot(x, y, "b", label="tech2")
        plt.ylabel('w/h')
        plt.xlabel('Nz')
        plt.legend()
        plt.show()

        for i in range(0, len(result4)):
            lists = sorted(result4[i].items())
            x, y = zip(*lists)  # unpack a list of pairs into two tuples
            plt.plot(x, y, c[i], label="tech" + str(i))
            # lists = sorted(result[1].items())
            # x, y = zip(*lists)  # unpack a list of pairs into two tuples
            # plt.plot(x, y, "y", label="tech1")
            # lists = sorted(result[2].items())
            # x, y = zip(*lists)  # unpack a list of pairs into two tuples
            # plt.plot(x, y, "b", label="tech2")
        plt.ylabel('lift util')
        plt.xlabel('Nz')
        plt.legend()
        plt.show()

        for i in range(0, len(result5)):
            lists = sorted(result5[i].items())
            x, y = zip(*lists)  # unpack a list of pairs into two tuples
            plt.plot(x, y, c[i], label="tech" + str(i))
            # lists = sorted(result[1].items())
            # x, y = zip(*lists)  # unpack a list of pairs into two tuples
            # plt.plot(x, y, "y", label="tech1")
            # lists = sorted(result[2].items())
            # x, y = zip(*lists)  # unpack a list of pairs into two tuples
            # plt.plot(x, y, "b", label="tech2")
        plt.ylabel('shuttle util')
        plt.xlabel('Nz')
        plt.legend()
        plt.show()

        for i in range(0, len(result6)):
            lists = sorted(result6[i].items())
            x, y = zip(*lists)  # unpack a list of pairs into two tuples
            plt.plot(x, y, c[i], label="tech" + str(i))
            # lists = sorted(result[1].items())
            # x, y = zip(*lists)  # unpack a list of pairs into two tuples
            # plt.plot(x, y, "y", label="tech1")
            # lists = sorted(result[2].items())
            # x, y = zip(*lists)  # unpack a list of pairs into two tuples
            # plt.plot(x, y, "b", label="tech2")
        plt.ylabel('sat util')
        plt.xlabel('Nz')
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
                                  Nli=34, Nsh=4, Nsa=4,
                                  bay_level=0,
                                  tech=0, strat=1, strat_par_x=1, strat_par_y=1)
        t_par = TraceParameter(sim_time=3600 * 3, types=[0.4, 0.3, 0.3], int_mean=25, start_fullness=0,
                               seed=1023)
        res = Test.test(parameter=par, trace_parameter=t_par, log=False)
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


    start_time = time.time()
    only_plot()
    print(time.time() - start_time)
