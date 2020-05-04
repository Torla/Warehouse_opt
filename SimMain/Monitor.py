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
            self.mean_task_wait = 1000000000
            self.mean_task_op_time = 1000000000
            self.mean_task_tot_time = 1000000000
            self.Th = 0
            self.completeness = 0
            self.working_time = 1000000000
            self.task_done = 0
            self.time_per_task = 1000000000
            self.energy_consumed = 1000000000
            self.energy_per_task = 1000000000
            self.area = 1000000000
            self.volume = 1000000000
            self.Nx = 10000000000
            self.Ny = 10000000000
            self.Nz = 10000000000
            self.num_lifts = 1000000000
            self.num_shuttles = 1000000000
            self.num_sats = 1000000000
            self.lifts_util_proc = 1000000000
            self.shut_util_proc = 1000000000
            self.sat_util_proc = 1000000000
            self.lifts_util = 1000000000
            self.shut_util = 1000000000
            self.sat_util = 1000000000
            self.single_CT = 1000000000
            self.double_CT = 1000000000
            self.single_CT_V = 1000000000
            self.double_CT_V = 1000000000
            self.single_CT_E = 1000000000
            self.double_CT_E = 1000000000
            self.strat_param = 1000000000

        def __str__(self):
            return "Average task wait: " + str(self.mean_task_wait) \
                   + "\nAverage task op time: " + str(self.mean_task_op_time) \
                   + "\nAverage task tot time: " + str(self.mean_task_tot_time) \
                   + "\nTh: " + str(3600 / self.mean_task_tot_time) \
                   + "\ntask done: " + str(self.task_done) \
                   + "\nEnergy consumed: " + str(self.energy_consumed / 1000) + " KW/h" \
                   + "\nEnergy consumed per tasks: " + str(self.energy_per_task) + " w/h" \
                   + "\nWorking time: " + str(self.working_time) \
                   + "\nTime per task: " + str(self.time_per_task) \
                   + "\nArea: " + str(self.area) \
                   + "\nVolume: " + str(self.volume) \
                   + "\nLifts: " + str(self.num_lifts) \
                   + "\nShuttles: " + str(self.num_shuttles) \
                   + "\nSats: " + str(self.num_sats) \
                   + "\nLifts util: " + str(self.lifts_util_proc) + " / " + str(self.lifts_util) \
                   + "\nShuttles util: " + str(self.shut_util_proc) + " / " + str(self.shut_util) \
                   + "\nSats util: " + str(self.sat_util_proc) + " / " + str(self.sat_util) \
                   + "\nSingle cycle: " + str(self.single_CT) + " var: " + str(self.single_CT_V) \
                   + "\nDouble cycle: " + str(self.double_CT) + " var: " + str(self.double_CT_V) \
                   + "\nSingle cycle energy: " + str(self.single_CT_E) \
                   + "\nDouble cycle energy: " + str(self.double_CT_E) \
                   + "\nStrat par: " + str(self.strat_param)

    def __init__(self, sim):
        assert isinstance(sim, Simulation)
        self.sim = sim
        self.due_tasks = 0
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

        res.Nx = par.Nx
        res.Ny = par.Ny
        res.Nz = par.Nz

        # abbuona qualche task non fatto all fine per consistenza
        task_done = len(self.tasks)
        if self.due_tasks != task_done and (
                (self.due_tasks - task_done) / self.due_tasks < 0.05 or self.due_tasks - task_done < par.Nli):
            task_done = self.due_tasks

        res.completeness = task_done / self.due_tasks

        res.task_done = task_done

        res.mean_task_tot_time = self.sim.now / task_done
        res.Th = 3600 / res.mean_task_tot_time
        res.time_per_task = np.average(self.tasks)
        if not self.sim.stop:
            self.sim.working_time += self.sim.now - self.sim.start
            self.sim.stop = True
        res.working_time = self.sim.working_time if self.sim.working_time != 0 else self.sim.now
        res.mean_task_op_time = res.working_time / task_done
        res.energy_consumed = sum(
            [i.energyConsumed for i in
             list(filter(lambda x: isinstance(x, MovableResource), self.sim.all_res.values()))])

        res.energy_per_task = res.energy_consumed / task_done

        res.area = par.Nx * par.Nz
        res.volume = res.area * par.Ny

        res.num_lifts = par.Nli
        res.num_shuttles = par.Nsh
        res.num_sats = par.Nsa

        if len(self.single_cycle) > 0:
            res.single_CT = np.average(self.single_cycle)
            res.single_CT_V = np.var(self.single_cycle)
            res.single_CT_E = np.average(self.single_cycle_e)

        if len(self.double_cycle) > 0:
            res.double_CT = np.average(self.double_cycle)
            res.double_CT_V = np.var(self.double_cycle)
            res.double_CT_E = np.average(self.double_cycle_e)

        res.lifts_util_proc = np.average(
            [i.util_proc for i in self.sim.find_performer(lambda x: isinstance(x, Lift), False)]) / res.working_time
        res.shut_util_proc = np.average(
            [i.util for i in self.sim.find_performer(lambda x: isinstance(x, Shuttle), False)]) / res.working_time
        res.sat_util_proc = np.average(
            [i.util for i in self.sim.find_performer(lambda x: isinstance(x, Satellite), False)]) / res.working_time
        res.lifts_util = np.average(
            [i.blocked_time for i in self.sim.find_performer(lambda x: isinstance(x, Lift), False)]) / res.working_time
        res.shut_util = np.average(
            [i.blocked_time for i in
             self.sim.find_performer(lambda x: isinstance(x, Shuttle), False)]) / res.working_time
        res.sat_util = np.average(
            [i.blocked_time for i in
             self.sim.find_performer(lambda x: isinstance(x, Satellite), False)]) / res.working_time
        if par.strategy_par_y != 0:
            res.strat_param = par.strategy_par_x / par.strategy_par_y
        else:
            res.strat_param = -1 if par.strategy_par_x == 0 else 10
        return res
