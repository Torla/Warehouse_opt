from enum import Enum
from functools import wraps

import simpy
from simpy import Container

from IdeaSim.Manager import Manager
from IdeaSim.Resources import Resources, Resource, Performer


class Simulation(simpy.Environment):
    class Logger:
        def __init__(self, env):
            self.env = env
            self.enabled = True

        class Type(Enum):
            NORMAL = ""
            HEADER = '\033[95m'
            BLUE = '\033[94m'
            WARNING = '\033[93m'
            GREEN = '\033[92m'
            FAIL = '\033[91m'
            UNDERLINE = '\033[4m'

        def enable(self, value):
            self.enabled = value

        def log(self, msg, indent=0, type=Type.NORMAL):
            if not self.enabled:
                return
            s = str(self.env.now) + ":" + " " * indent + msg
            print(type.value + s + '\033[0m')

    class Mutex(Container):
        def __init__(self, env):
            super().__init__(env, capacity=1, init=1)

        def lock(self):
            return self.get(1)

        def unlock(self):
            return self.put(1)

    def __init__(self, status=None):
        super().__init__()
        self.logger = Simulation.Logger(self)

        self.manager = Manager(self)

        self.free_res = Resources(self)
        self.free_map = {}
        self.all_res = {}
        self.all_performer = []

        self.__status__ = status

        self.global_mutex = Simulation.Mutex(self)

        # monitor

        self.start = 0
        self.working_time = 0
        self.stop = True

    # adding new not re-putting
    def add_res(self, res):
        assert isinstance(res, Resource)
        self.all_res[res.id] = res
        self.free_res.items.append(res)
        self.free_map[res.id] = True
        if isinstance(res, Performer):
            self.all_performer.append(res)

    def find_res_by_id(self, id, free=True):
        if not free:
            return self.all_res[id]
        return list(filter(lambda x: x.id == id, self.free_res.items))[0]

    def find_res(self, func, free=True) -> list:
        l = self.free_res.items if free else self.all_res.values()
        return list(filter(lambda x: func(x), l))

    def find_performer(self, func, free=True) -> list:
        if free:
            return list(filter(lambda x: self.is_free(x) and func(x), self.all_performer))
        else:
            return list(filter(lambda x: func(x), self.all_performer))

    def get_res_by_id(self, id):
        # monitor
        if self.stop:
            self.stop = False
            self.start = self.now

        # not monitor
        return self.free_res.get(lambda x: x.id == id)

    def get_res(self, func, sort_by=None):
        # monitor
        if self.stop:
            self.stop = False
            self.start = self.now
        # not monitor
        if sort_by is not None:
            assert callable(sort_by)
            l = self.find_res(func)
            l.sort(key=sort_by)
            if len(l) != 0:
                return self.get_res_by_id(l[0].id)
        return self.free_res.get(lambda x: func(x))

    def is_free(self, res):
        assert isinstance(res, Resource)
        return self.free_map[res.id]

    def put_res(self, res):
        assert (isinstance(res, Resource))
        assert isinstance(res, Resource)
        if len(self.free_res.items) == len(self.all_res) - 1:
            self.working_time += self.now - self.start
            self.stop = True
        return self.free_res.put(res)

    def wait(self, delay):
        return self.timeout(delay)

    def get_status(self):
        return self.__status__

    def modify_status(self):
        self.logger.log("Status change", 2)
        self.manager.activate()
        return self.__status__
