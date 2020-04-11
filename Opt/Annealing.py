import random

import numpy
from simanneal import Annealer
import Opt.Optimization


def annealing(opt_par, f_par, mut,n_process):
    class Ann(Annealer):
        def __init__(self, opt_par, fitness_par, mut, array=None) -> None:
            # super().__init__()
            self.solution = Opt.Optimization.Solution(opt_par, fitness_par, array)
            self.state = list(self.solution)
            self.mut = mut

        def move(self):
            i = random.randint(0, len(self.state) - 1)
            self.state[i] += self.state[i] * self.mut * numpy.random.randn(1)[0]
            self.state[i] = 0 if self.state[i] < 0 else self.state[i]
            self.state[i] = 1 if self.state[i] > 1 else self.state[i]
            self.solution = Opt.Optimization.Solution(self.solution.opt_par, self.solution.fitness_par,
                                                      self.state)

        def energy(self):
            return self.solution.get_fitness()

    Opt.Optimization.Solution.set_process_pool(n_process)

    ann = Ann(opt_par, f_par, mut, None)

    ann.Tmax = 1000
    ann.Tmin = 10
    ann.steps = 20
    ann.updates = 0

    while True:
        a, b = ann.anneal()
        yield Opt.Optimization.Solution(opt_par, f_par, a)
        ann.state = a
        ann.solution = Opt.Optimization.Solution(opt_par, f_par, a)
