import itertools
from enum import Enum

from simpy import Container

from IdeaSim import Simulation
from IdeaSim.Resources import Performer


class Action:
    new_id = itertools.count()

    def __init__(self, action_graph, action_type, who, sort_by=None, param=None, after=None, condition=None,
                 on_false=None, branch=None):
        self.id = next(self.new_id)
        assert isinstance(action_graph, ActionsGraph)
        action_graph.actions[self.id] = self
        self.action_graph = action_graph
        self.actionType = action_type
        self.who = who
        assert isinstance(param, dict) or param is None
        self.sort_by = sort_by
        self.param = {} if param is None else param
        assert isinstance(after, list) or after is None
        self.after = [] if after is None else after
        self.condition = condition
        self.on_false = on_false
        self.branch = branch

    @staticmethod
    def abort(action, sim):
        raise Executor.AbortExecution

    def __str__(self) -> str:
        return str(self.actionType) + str(self.param)


class Block(Action):

    def __init__(self, action_graph, who, sort_by=None, param=None, after=None, branch=None):
        super().__init__(action_graph, "Block", who, sort_by=sort_by, param=param, after=after, branch=branch)


class Free(Action):

    def __init__(self, action_graph, who, sort_by=None, param=None, after=None, branch=None):
        super().__init__(action_graph, "Free", who, sort_by=sort_by, param=param, after=after, branch=branch)


class GenerateEvent(Action):

    def __init__(self, action_graph, event, after=None, branch=None):
        super().__init__(action_graph, action_type="Event generation", who=None, sort_by=None, param=None, after=after,
                         branch=branch)
        self.event = event


class Branch(Action):

    def __init__(self, action_graph, after=None, condition=None, on_false=None, branch=None):
        super().__init__(action_graph, action_type=None, who=None, sort_by=None, param=None, after=after,
                         condition=condition, on_false=on_false, branch=branch)


class ActionsGraph:
    new_id = itertools.count()

    def __init__(self, sim, task):
        assert isinstance(sim, Simulation.Simulation)
        self.id = next(self.new_id)
        self.sim = sim
        self.actions = {}
        self.task = task
        self.global_mutex_property = False


class Executor:
    def __init__(self, sim, action_tree):

        assert isinstance(action_tree, ActionsGraph)
        self.action_tree = action_tree
        self.sim = sim
        sim.process(self.run())
        self.aborted = False
        self.branches = {}

    class AbortExecution(Exception):

        def __init__(self) -> None:
            super().__init__()

    def run(self):
        wait = None
        taken_inf = []
        completed_flags = {}

        start = self.sim.now

        for action_id in self.action_tree.actions.keys():
            completed_flags[action_id] = Container(self.sim)

        for action in self.action_tree.actions.values():
            self.sim.process(
                self.execute(self.action_tree, action, taken_inf, self.sim, completed_flags))

        for flag in completed_flags.values():
            if wait is None:
                wait = flag.get(1)
            else:
                wait = wait & flag.get(1)
        yield wait

        if self.aborted:
            for res in taken_inf:
                self.sim.put_res(res)

        taken_inf.clear()

        if len(taken_inf) != 0:
            raise Exception("Resources not free at end of task")

        self.sim.manager.activate()

        # monitor
        if not self.aborted:
            self.sim.get_status().monitor.tasks.append([self.sim.now - start])

    def execute(self, action_tree, action, taken_inf, sim, completed_flags):
        assert isinstance(action, Action)
        assert isinstance(sim, Simulation.Simulation)
        wait = None
        try:
            for action_id in action.after:
                if wait is None:
                    wait = completed_flags[action_id].get(1)
                else:
                    wait = wait & completed_flags[action_id].get(1)
            if wait is not None:
                yield wait
            if not action_tree.global_mutex_property:
                action_tree.sim.global_mutex.lock()
        except KeyError:
            sim.logger.log("waiting for non existing action", 0, sim.logger.Type.FAIL)
        finally:
            if not action_tree.global_mutex_property:
                action_tree.sim.global_mutex.unlock()

        if self.aborted:
            yield completed_flags[action.id].put(float('inf'))
            return

        elif action.branch is not None and action.branch not in self.branches:
            yield completed_flags[action.id].put(float('inf'))
            return

        elif action.branch in self.branches:
            if not self.branches[action.branch]:
                yield completed_flags[action.id].put(float('inf'))
                return

        try:
            if action.condition is not None:
                assert callable(action.condition)
                if not (action.condition(sim, taken_inf)):
                    if action.on_false is not None:
                        assert callable(action.on_false)
                        yield completed_flags[action.id].put(float('inf'))
                        yield action.on_false(action, sim)
                    if isinstance(action, Branch):
                        self.branches[action.id] = False
                    yield completed_flags[action.id].put(float('inf'))
                    return

            if isinstance(action, Block):
                if callable(action.who):
                    res = yield sim.get_res(action.who, action.sort_by)
                    taken_inf.append(res)
                    yield completed_flags[action.id].put(float('inf'))
                    res.last_blocked = sim.now
                    sim.logger.log("blocking  " + str(
                        res) + " for " + str(action.action_graph.id),
                                   7)
                else:
                    yield sim.get_res_by_id(action.who)
                    taken_inf.append(sim.find_res_by_id(action.who, free=False))
                    sim.find_res_by_id(action.who, free=False).last_blocked = sim.now
                    yield completed_flags[action.id].put(float('inf'))
                    sim.logger.log("blocking  " + str(
                        sim.find_res_by_id(action.who, free=False)) + " for " + str(action.action_graph.id),
                                   7)

            elif isinstance(action, Free):
                if callable(action.who):
                    l = list(filter(lambda x: action.who(x), taken_inf))
                    if action.sort_by is None:
                        pass
                    else:
                        l.sort(key=lambda x: action.sort_by(x))
                    action.who = l[0].id
                inf = list(filter(lambda x: x.id == action.who, taken_inf))[0]
                yield sim.put_res(inf)
                taken_inf.remove(inf)
                sim.find_res_by_id(action.who, free=False) \
                    .blocked_time += sim.now - sim.find_res_by_id(action.who, free=False).last_blocked
                yield completed_flags[action.id].put(float('inf'))
                # manager is activated after anything is free
                sim.logger.log("Free " + str(
                    sim.find_res_by_id(inf.id, free=False)) + " for " + str(action.action_graph.id), 7)
                self.sim.manager.activate()

            elif isinstance(action, GenerateEvent):
                action.event.launch()
                sim.logger.log(str(action) + " launches event " + str(action.event), 7)

            elif isinstance(action, Branch):
                self.branches[action.id] = True
                yield completed_flags[action.id].put(float('inf'))

            else:
                try:
                    if callable(action.who):
                        l = list(filter(lambda x: action.who(x), taken_inf))
                        if action.sort_by is None:
                            pass
                        else:
                            l.sort(key=lambda x: action.sort_by(x))
                        action.who = l[0].id
                    yield self.sim.process(
                        list(filter(lambda x: x.id == action.who, taken_inf))[0].perform(action, taken_inf))
                except Performer.IllegalAction as err:
                    sim.logger.log(str(err), type=sim.logger.Type.FAIL)
                except KeyError as err:
                    sim.logger.log("Action parameter not defined" + str(err), type=sim.logger.Type.FAIL)
                except IndexError as err:
                    sim.logger.log("Performer not blocked " + str(err), type=sim.logger.Type.FAIL)

                yield completed_flags[action.id].put(float('inf'))
        except Executor.AbortExecution:
            self.aborted = True
