from SimMain.Logger import Logger
from Task.Task import Task
from IdeaSim.Simulation import Simulation
from IdeaSim.Event import Event


class TaskDispatcher:
    def __init__(self, simulation, tasks):
        assert (isinstance(simulation, Simulation))
        self.sim = simulation
        self.tasks = tasks
        self.run()

    # this unpack the order to tasks. The existing queue can be modified

    def add_future_task(self, time, task):
        self.tasks[time] = task

    def run(self):
            for time in self.tasks.keys():
                Event(self.sim, time, "new_task", param={"task": self.tasks[time]})
