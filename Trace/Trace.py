from random import randint

from Task.Item import Item
import jsonpickle
import numpy as np

# todo write a real one
from Task.Task import Task, OrderType


def trace_generator_old(trace_par) -> {}:
    assert isinstance(trace_par, TraceParameter)
    ret = {}
    time = 0
    np.random.seed(trace_par.seed if trace_par.seed is not None else np.random.randint(0, 10000000))

    warehouse = {}

    while time < trace_par.sim_time:
        time += round(np.random.exponential(scale=trace_par.int_mean))

        item_type = "Tipo" + str(np.random.choice([i for i in range(0, len(trace_par.types))], p=trace_par.types))

        if item_type not in warehouse or warehouse[item_type] < 1:
            task = Task(Item(item_type), OrderType.DEPOSIT)
            if item_type in warehouse:
                warehouse[item_type] += 1
            else:
                warehouse[item_type] = 1

        else:
            task = Task(Item(item_type), OrderType.DEPOSIT if np.random.randint(0, 1) else OrderType.RETRIEVAL)
            warehouse[item_type] += 1 if task.order_type == OrderType.DEPOSIT else -1
        ret[time] = task
    return ret


def trace_generator(trace_par) -> {}:
    assert isinstance(trace_par, TraceParameter)
    ret = {}
    time = 0
    np.random.seed(trace_par.seed if trace_par.seed is not None else np.random.randint(0, 10000000))

    warehouse = {}

    while time < trace_par.sim_time:
        time += round(np.random.exponential(scale=trace_par.int_mean))

        item_type = np.random.choice(a=[i for i in trace_par.types.keys()], p=[i for i in trace_par.types.values()])


        task = Task(Item(item_type), OrderType.RETRIEVAL if np.random.randint(0, 1) else OrderType.RETRIEVAL)

        ret[time] = task
    return ret


class TraceParameter:
    def __init__(self, sim_time, types, int_mean, start_fullness, seed) -> None:
        self.types = types
        self.sim_time = sim_time
        self.seed = seed
        self.start_fullness = start_fullness
        self.int_mean = int_mean
