import random

import numpy

from Opt import Optimization
from Opt.Optimization import Solution


def opt(par, f_par, start, neighborhood, mut, n_process):
    Solution.set_process_pool(n_process)

    class Sol(Optimization.Solution):
        def __init__(self, par, f_par, array=None):
            super().__init__(par, f_par, array)
            self.mut = mut

        def neigh(self, n):
            for i in range(0, n):
                y = Sol(self.opt_par, self.fitness_par, self)
                i = random.randint(0, len(self) - 1)
                y[i] += y[i] * self.mut * numpy.random.randn(1)[0]
                y[i] = 0 if y[i] < 0 else y[i]
                y[i] = 1 if y[i] > 1 else y[i]
                yield y

    p = [Sol(par, f_par) for i in range(0, start)]

    while True:
        yield min(p, key=lambda x: x.get_fitness())
        a = []
        for i in p:
            n = list(i.neigh(neighborhood))
            try:
                a.append(min(list(filter(lambda x: x.get_fitness() <= i.get_fitness(), n)),
                             key=lambda x: x.get_fitness()))
            except ValueError:
                # a.append(i)
                continue
        if len(a) == 0:
            return
        p = a
