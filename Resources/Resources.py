import itertools

from simpy import FilterStore


class Resources(FilterStore):
    def __init__(self, env, capacity=float('inf')):
        super().__init__(env, capacity)


class Resource:
    new_id = itertools.count()

    def __init__(self, position, parameter):
        self.parameter = parameter
        self.position = position
        self.id = next(self.new_id)

