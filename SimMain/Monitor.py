import numpy as np

from IdeaSim.Resources import Movable
from IdeaSim.Simulation import Simulation
from Resources.Movement import MovableResource


class Monitor:
    class Results:
        def __init__(self):
            self.mean_task_wait = np.inf
            self.mean_task_op_time = np.inf
            self.mean_task_tot_time = np.inf
            self.working_time = np.inf
            self.time_per_task = np.inf
            self.energy_consumed = np.inf
            self.parr_ratio = 0

        def __str__(self):
            return "Average task wait: " + str(self.mean_task_wait) \
                   + "\nAverage task op time: " + str(self.mean_task_op_time) \
                   + "\nAverage task tot time: " + str(self.mean_task_tot_time) \
                   + "\nEnergy consumed: " + str(self.energy_consumed / 1000) + " KW/h" \
                   + "\nWorking time: " + str(self.working_time) \
                   + "\nTime per task: " + str(self.time_per_task) \
                   + "\nPararelization ratio: " + str(self.parr_ratio)

    def __init__(self, sim):
        assert isinstance(sim, Simulation)
        self.sim = sim
        self.tasks = []
        self.working_time = 0

    def get_result(self) -> Results:
        res = Monitor.Results()

        res.mean_task_wait = 0
        res.mean_task_tot_time = self.sim.now / len(self.tasks)
        res.time_per_task = np.average(self.tasks)
        if not self.sim.stop:
            self.sim.working_time += self.sim.now - self.sim.start
        res.working_time = self.sim.working_time if self.sim.working_time != 0 else self.sim.now
        res.mean_task_op_time = res.working_time / len(self.tasks)
        res.energy_consumed = sum(
            [i.energyConsumed for i in list(filter(lambda x: isinstance(x, MovableResource), self.sim.all_res.values()))])
        res.parr_ratio = res.time_per_task / res.mean_task_op_time
        return res
