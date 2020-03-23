import math
from overrides import overrides

import Resources.EnergyModel
from Resources.Resources import Resource
from SimMain.Logger import Logger
from SimMain.SimulationParameter import SimulationParameter
import numpy as np


class Position:
    def __init__(self, section=0, level=0, x=0, z=0):
        self.z = z
        self.x = x
        self.level = level
        self.section = section

    def __str__(self):
        return " level: " + str(self.level) + " x: " + str(self.x) + " z: " + str(self.z)


class MovableResource(Resource):
    def __init__(self, position, acc, max_v, par):
        super().__init__(position, par)
        self.max_v = max_v
        self.acc = acc
        self.content = None
        self.energyConsumed = 0
        self.weight = 0

    def move(self, position, parameter) -> int:
        d = distance(self.position, position, parameter)

        acc_time = self.max_v / self.acc
        acc_space = self.max_v * acc_time * acc_time * 2

        if d > acc_space:
            time = acc_time * 2 + (d - acc_space) / self.max_v
        else:
            time = math.sqrt(d / self.acc)

        energy_consumed = Resources.EnergyModel.energy(self.position, position, parameter, self.__weight__())
        self.energyConsumed += energy_consumed

        Logger.log(
            str(self) + " move " + str(d) + "m in " + str(time) + "s w:" + str(self.__weight__()) + "Kg E:" + str(
                energy_consumed / 1000) + "KW/h (" + str(
                self.position) + ")->(" + str(
                position) + ")",
            20)

        self.position = Position(position.section, position.level, position.x, position.z)

        if self.content is not None and isinstance(self.content, MovableResource):
            self.content.__drag__(position)

        return int(self.smart_round(time))

    def __drag__(self, position):
        Logger.log("with " + str(self), 30)
        self.position = Position(position.section, position.level, position.x, position.z)
        if self.content is None or not isinstance(self.content, MovableResource):
            return
        self.content.__drag__(position)

    @staticmethod
    def smart_round(x):
        precision = 10000000
        m = x - math.floor(x)
        if np.random.randint(0, precision) > m * precision:
            return math.floor(x)
        else:
            return math.ceil(x)

    def __weight__(self):
        return self.weight + (self.content.__weight__() if self.content is not None else 0)


def distance(p1, p2, parameter) -> float:
    assert isinstance(parameter, SimulationParameter)
    assert isinstance(p1, Position)
    assert isinstance(p2, Position)
    if p1.section != p2.section and p1.section is not None and p2.section is not None:
        return np.inf
    if p1.level != p2.level:
        ret = abs(p1.level - p2.level) * parameter.Ly
    elif p1.x != p2.x:
        ret = abs(p1.x - p2.x) * parameter.Lx
    else:
        ret = abs(p1.z - p2.z) * parameter.Lz

    return ret
