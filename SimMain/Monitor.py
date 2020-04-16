import numpy as np

from IdeaSim.Resources import Movable
from IdeaSim.Simulation import Simulation
from Resources.Lift import Lift
from Resources.Movement import MovableResource
from Resources.Satellite import Satellite
from Resources.Shuttle import Shuttle


class Monitor:
    class Results:
        def __init__(self):
            self.mean_task_wait = np.inf
            self.mean_task_op_time = np.inf
            self.mean_task_tot_time = np.inf
            self.working_time = np.inf
            self.time_per_task = np.inf
            self.energy_consumed = np.inf
            self.area = np.inf
            self.volume = np.inf
            self.num_lifts = 0
            self.num_shuttles = 0
            self.num_sats = 0
            self.lifts_util = 0
            self.shut_util = 0
            self.sat_util = 0
            self.single_CT = 0
            self.double_CT = 0
            self.single_CT_E = 0
            self.double_CT_E = 0
            # todo energia per ciclo (if
            #  easy), utilizzazione (per tipo)

        def __str__(self):
            return "Average task wait: " + str(self.mean_task_wait) \
                   + "\nAverage task op time: " + str(self.mean_task_op_time) \
                   + "\nAverage task tot time: " + str(self.mean_task_tot_time) \
                   + "\nEnergy consumed: " + str(self.energy_consumed / 1000) + " KW/h" \
                   + "\nWorking time: " + str(self.working_time) \
                   + "\nTime per task: " + str(self.time_per_task) \
                   + "\nArea: " + str(self.area) \
                   + "\nVolume: " + str(self.volume) \
                   + "\nLifts: " + str(self.num_lifts) \
                   + "\nShuttles: " + str(self.num_shuttles) \
                   + "\nSats: " + str(self.num_sats) \
                   + "\nLifts util: " + str(self.lifts_util) \
                   + "\nShuttles util: " + str(self.shut_util) \
                   + "\nSats util: " + str(self.sat_util) \
                   + "\nSingle cycle: " + str(self.single_CT) \
                   + "\nDouble cycle: " + str(self.double_CT) \
                   + "\nSingle cycle energy: " + str(self.single_CT_E) \
                   + "\nDouble cycle energy: " + str(self.double_CT_E)

    def __init__(self, sim):
        assert isinstance(sim, Simulation)
        self.sim = sim
        self.tasks = []
        self.single_cycle = []
        self.double_cycle = []
        self.single_cycle_e = []
        self.double_cycle_e = []
        self.working_time = 0

    def get_result(self) -> Results:
        par = self.sim.get_status().parameter

        res = Monitor.Results()

        res.mean_task_wait = 0
        res.mean_task_tot_time = self.sim.now / len(self.tasks)
        res.time_per_task = np.average(self.tasks)
        if not self.sim.stop:
            self.sim.working_time += self.sim.now - self.sim.start
        res.working_time = self.sim.working_time if self.sim.working_time != 0 else self.sim.now
        res.mean_task_op_time = res.working_time / len(self.tasks)
        res.energy_consumed = sum(
            [i.energyConsumed for i in
             list(filter(lambda x: isinstance(x, MovableResource), self.sim.all_res.values()))])

        res.area = par.Nx * par.Nz
        res.volume = res.area * par.Ny

        res.num_lifts = par.Nli
        res.num_shuttles = par.Nsh
        res.num_sats = par.Nsa

        res.single_CT = np.average(self.single_cycle)
        res.double_CT = np.average(self.double_cycle)
        # res.single_CT_E = np.average(self.single_cycle_e)
        # res.double_CT_E = np.average(self.double_cycle_e)

        res.lifts_util = np.average(
            [i.util for i in self.sim.find_res(lambda x: isinstance(x, Lift))]) / res.working_time
        res.shut_util = np.average(
            [i.util for i in self.sim.find_res(lambda x: isinstance(x, Shuttle))]) / res.working_time
        res.sat_util = np.average(
            [i.util for i in self.sim.find_res(lambda x: isinstance(x, Satellite))]) / res.working_time

        return res
