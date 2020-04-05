import random
import time




from IdeaSim.Simulation import Simulation
from SimMain.Logger import Logger
from SimMain.SimulationParameter import SimulationParameter
from Trace.Trace import trace_generator, TraceParameter
from Warehouse.Warehouse import Warehouse


class Test:
    @staticmethod
    def test(parameter, trace_parameter):
        class Status:
            def __init__(self,parameter):
                self.parameter = parameter
        sim = Simulation(Status(parameter))
        # env = simpy.RealtimeEnvironment(0, 0.1, False)
        Logger.enable(False)
        Logger.set_env(sim)
        # warehouse = Warehouse(env, parameter, trace_load("trace1.json"))
        warehouse = Warehouse(sim, parameter, trace_generator(trace_parameter))
        sim.run()

#        Logger.log(str(warehouse.monitor.get_result()))
        # warehouse.monitor.plot(definition=3600)

        #return warehouse.monitor.get_result()


if __name__ == '__main__':
    random.seed(time.time())
    random.seed(123)
    Logger.enable(True)
    par = SimulationParameter(Nx=8, Ny=8, Nz=80,
                              Lx=5, Ly=5, Lz=5, Cy=1,
                              Ax=0.8, Vx=4, Ay=0.8, Vy=0.9, Az=0.7, Vz=1.20,
                              Wli=1850, Wsh=850, Wsa=350,
                              Cr=0.02, Fr=1.15, rendiment=0.9,
                              Nli=4, Nsh=4, Nsa=1,
                              bay_level=1.5,
                              tech=1, strat=0)
    t_par = TraceParameter(sim_time=10000, type_num=5, int_mean=10, num_mean=100, mean_present=10, seed=[35, 64])
    Test.test(parameter=par, trace_parameter=t_par)
