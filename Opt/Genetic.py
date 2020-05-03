import random

import numpy
from numpy import average

import Opt.Optimization


def opt(opt_par, t_par, f_par, pop_size, pos_swap, mut, mut_change, mut_perc, bottle_neck_prob, bottle_neck_swap,
        n_process):
    Opt.Optimization.Solution.set_process_pool(n_process)

    class Chromosome(Opt.Optimization.Solution):

        def __init__(self, opt_par, t_par, fitness_par, mut, array=None) -> None:
            self.mut = mut
            super().__init__(opt_par, t_par, fitness_par, array)
            if array is not None:
                self.mutation()

        def mutation(self):
            seleted = []
            for i in range(0, len(self)):
                if i <= len(self) * mut_perc:
                    seleted.append(1)
                else:
                    seleted.append(0)
            random.shuffle(seleted)
            for i in range(0, len(self)):
                if seleted[i] == 1:
                    self[i] += mut * numpy.random.randn()
                    self[i] = 0 if self[i] < 0 else self[i]
                    self[i] = 1 if self[i] > 1 else self[i]

        @staticmethod
        def crossover(c1, c2):
            child = []
            for i in range(0, len(c1)):
                child.append(c1[i] if random.randint else c2[i])
            return Chromosome(opt_par, t_par, f_par, c1.mutation, child)

    class Population:
        def __init__(self, opt_par, t_par, f_par, mut, size, pop_swap):
            self.pop_swap = pop_swap
            self.pop = [Chromosome(opt_par, t_par, f_par, mut) for i in range(0, size)]

        def generation(self):

            pop = []
            pw = self.pop_swap if random.uniform(0, 1) > bottle_neck_prob else bottle_neck_swap
            self.pop = sorted(self.pop, key=lambda x: x.get_fitness())
            for i in range(0, round(len(self.pop) * (1 - pw))):
                pop.append(self.pop[i])
            i = 0
            for couple in self.gen_couple():
                pop.append(Chromosome.crossover(couple[0], couple[1]))
                i = i + 1
                if i >= round(len(self.pop) * pw):
                    break
            self.pop = pop

        def gen_couple(self):
            w = list(map(lambda x: 1 / x.get_fitness(), self.pop))
            for i in range(0, len(w)):
                if i == 0:
                    pass
                else:
                    w[i] = w[i] + w[i - 1]

            w = list(map(lambda x: x / w[len(w) - 1], w))
            ret = []
            while True:
                for j in range(0, 2):
                    r = random.uniform(0, 1)
                    for i in range(0, len(w)):
                        if i == 0 and r <= w[i]:
                            ret.append(self.pop[i])
                        elif i != 0 and w[i - 1] < r <= w[i]:
                            ret.append(self.pop[i])
                yield ret

        def get_best(self):

            return sorted(self.pop, key=lambda x: x.get_fitness())[0]

    pop = Population(opt_par, t_par, f_par, mut, pop_size, pos_swap)
    while True:
        yield pop.get_best()
        mut += mut * mut_change
        pop.generation()
