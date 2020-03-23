from simpy import Container

from Manager.Action import ActionsGraph, ActionType
from Resources.Performer import Performer
from SimMain.Logger import Logger


class Executor:
    def __init__(self, env, action_tree, warehouse, manager):
        self.warehouse = warehouse
        assert isinstance(action_tree, ActionsGraph)
        self.action_tree = action_tree
        self.manager = manager
        self.resources = warehouse.resources
        self.all_resources = warehouse.all_resources

        self.env = env
        env.process(self.run())

    def run(self):
        wait = None
        taken_inf = []
        completed_flags = {}

        for action_id in self.action_tree.actions.keys():
            completed_flags[action_id] = Container(self.env)

        for action in self.action_tree.actions.values():
            self.env.process(
                self.execute(action, taken_inf, self.resources, self.all_resources, completed_flags, self.manager))

        for flag in completed_flags.values():
            if wait is None:
                wait = flag.get(1)
            else:
                wait = wait & flag.get(1)
        yield wait

        for task in self.action_tree.tasks:
            Logger.log("task performed: " + str(task), 5)
            self.warehouse.monitor.task_action[task.id]["end"] = self.env.now

        if len(taken_inf) != 0:
            raise Exception("Resources not free at end of task")

        yield self.manager.activation.put(1)

    def execute(self, action, taken_inf, resources, all_resorces, completed_flags, manager):
        wait = None
        try:
            for action_id in action.after:
                if wait is None:
                    wait = completed_flags[action_id].get(1)
                else:
                    wait = wait & completed_flags[action_id].get(1)
            if wait is not None:
                yield wait
        except KeyError:
            Logger.log("waiting for non existing action", 0, Logger.Type.FAIL)

        if action.actionType == ActionType.BLOCK:
            yield resources.get(lambda x: x.id == action.who)
            taken_inf.append(list(filter(lambda x: x.id == action.who, all_resorces))[0])
            completed_flags[action.id].put(float('inf'))
            Logger.log("blocking  " + str(
                list(filter(lambda x: x.id == action.who, all_resorces))[0]) + " for " + str(self.action_tree.tasks[0]),
                       7)

        elif action.actionType == ActionType.FREE:
            inf = list(filter(lambda x: x.id == action.who, taken_inf))[0]
            yield resources.put(inf)
            taken_inf.remove(inf)
            completed_flags[action.id].put(float('inf'))
            # manager is activated after anything is free
            Logger.log("Free " + str(
                list(filter(lambda x: x.id == action.who, all_resorces))[0]) + " for " + str(self.action_tree.tasks[0]),
                       7)
            yield self.manager.activation.put(1)

        else:
            try:
                yield self.env.process(
                    list(filter(lambda x: x.id == action.who, taken_inf))[0].perform(action, taken_inf, all_resorces))
            except Performer.IllegalAction as err:
                Logger.log(str(err), type=Logger.Type.FAIL)
            except KeyError as err:
                Logger.log("Action parameter not defined" + str(err), type=Logger.Type.FAIL)
            except IndexError as err:
                Logger.log("Performer not blocked " + str(err), type=Logger.Type.FAIL)

            completed_flags[action.id].put(float('inf'))
