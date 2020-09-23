from IdeaSim.Simulation import Simulation
from IdeaSim.Event import Event


class TaskDispatcher:
    def __init__(self, simulation, tasks):
        assert (isinstance(simulation, Simulation))
        self.sim = simulation
        self.tasks = tasks
        self.run()

    def add_future_task(self, time, task):
        self.tasks[time] = task
        Event(self.sim, time, "new_task", param={"task": self.tasks[time]})

    def run(self):
        for time in self.tasks.keys():
            Event(self.sim, time, "new_task", param={"task": self.tasks[time]})

        self.sim.get_status().monitor.due_tasks = len(self.tasks)
