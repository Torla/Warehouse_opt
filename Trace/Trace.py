from random import randint

from Task.Item import Item
import jsonpickle
import numpy as np

# todo write a real one
from Task.Task import Task, OrderType


def trace_generator(trace_par) -> {}:
    assert isinstance(trace_par, TraceParameter)
    ret = {}
    time = 0
    np.random.seed(trace_par.seed if trace_par.seed is not None else np.random.randint(0, 10000000))

    warehouse = {}

    while time < trace_par.sim_time:
        time += round(np.random.exponential(scale=trace_par.int_mean))

        num = np.random.exponential(trace_par.num_mean)
        num = round(1 if num <= 0 else num)

        item_type = "Tipo" + str(randint(0, np.random.randint(0, trace_par.type_num)))

        task = None
        if sum(warehouse.values()) < trace_par.mean_present or item_type not in warehouse \
                or warehouse[item_type] < 1:
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


class TraceParameter:
    def __init__(self, sim_time, type_num, int_mean, num_mean, mean_present, seed) -> None:
        self.type_num = type_num
        self.sim_time = sim_time
        self.seed = seed
        self.mean_present = mean_present
        self.num_mean = num_mean
        self.int_mean = int_mean
