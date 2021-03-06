from IdeaSim.Event import Event
from IdeaSim.Actions import ActionsGraph, Action, Block, Free, Branch
from IdeaSim.Resources import Resources
from Resources.ActionType import ActionType
from Resources.Bay import Bay
from Resources.Movement import distance, Position
from Resources.Channel import Channel
from Resources.Lift import Lift
from Resources.Satellite import Satellite
from Resources.Shuttle import Shuttle
from SimMain.SimulationParameter import SimulationParameter
from Task.Task import Task, OrderType
from IdeaSim.Simulation import Simulation
from IdeaSim.Manager import Manager
import numpy as np


# first number:
#   0 -> only lift
#   1 -> lift + shuttle
#   2 -> all
# second number strategy

class Strategy:
    class NoPlaceTODeposit(Manager.RetryLater):
        def __init__(self, task, delay=None):
            super().__init__(delay=delay)
            self.task = task

    class NoItemToTake(Manager.RetryLater):
        def __init__(self, task, delay=None):
            super().__init__(delay=delay)
            self.task = task

    class NeedToWait(Manager.RetryLater):
        def __init__(self, task):
            self.task = task

    @staticmethod
    def select_type(l, tipe):
        return list(filter(lambda x: isinstance(x, tipe), l))[0]

    bay = None

    @staticmethod
    def strategy(event) -> ActionsGraph:
        if Strategy.bay is None:
            Strategy.bay = event.sim.find_res(lambda x: isinstance(x, Bay))[0]
        assert isinstance(event, Event)
        event.sim.logger.log(
            "New task dispached " + str(event.param["task"].order_type) + " " + str(event.param["task"].item))
        parameter = event.sim.get_status().parameter
        try:
            selection = Strategy.__dict__["strategy" + str(parameter.strategy)] \
                .__func__(event.param["task"], event.sim, parameter)
        except KeyError as e:
            event.sim.logger.log("Strategy or technology selected is not defined", type=event.sim.Logger.Type.FAIL)
            exit(-1)
        return Strategy.implement(event.param["task"], selection, event.sim, parameter)

    @staticmethod
    def implement(task, channel_id, sim, parameter) -> ActionsGraph:
        assert isinstance(task, Task)
        assert isinstance(sim, Simulation)
        assert isinstance(channel_id, int)
        assert isinstance(parameter, SimulationParameter)
        try:
            return Strategy.__dict__["implement" + str(parameter.tech)] \
                .__func__(task, channel_id, sim, parameter)
        except KeyError:
            sim.logger.log("Technology selected is not defined", type=sim.Logger.Type.FAIL)
            exit(-1)

    @staticmethod
    def ab(action, sim):
        assert (isinstance(sim, Simulation))
        sim.logger.log("aborting " + str(action), type=sim.Logger.Type.WARNING)
        Event(sim, sim.now + 1, "new_task", param={"task": action.action_graph.task})
        Action.abort(action, sim)

    @staticmethod
    def implement0(task, channel_id, sim, parameter) -> ActionsGraph:
        assert isinstance(task, Task)
        assert isinstance(sim, Simulation)
        assert isinstance(channel_id, int)
        assert isinstance(parameter, SimulationParameter)
        r = ActionsGraph(sim, task)
        channel = sim.find_res_by_id(channel_id)
        if task.order_type == OrderType.DEPOSIT:
            block = Block(r, channel.id)
            block1 = Block(r, lambda x: isinstance(x, Satellite) and x.position.section == channel.position.section,
                           after=[block.id])
            block2 = Block(r, lambda x: isinstance(x, Shuttle) and x.position.section == channel.position.section,
                           after=[block1.id])
            block3 = Block(r, lambda x: isinstance(x, Lift) and x.position.section == channel.position.section,
                           after=[block2.id])

            fork_move = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite), param={"z": 0},
                               condition=lambda x, y: len(
                                   sim.find_res_by_id(channel_id, free=False).items) != sim.find_res_by_id(channel_id,
                                                                                                           free=False).capacity,
                               after=[block.id, block1.id, block2.id, block3.id])
            move = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift),
                          param={"level": Strategy.bay.position.level},
                          after=[fork_move.id])
            move1 = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": 0},
                           after=[fork_move.id])

            pick_up = Action(r, ActionType.GET_FROM_BAY, lambda x: isinstance(x, Satellite), param={"item": task.item},
                             after=[move1.id, move.id])

            move = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"level": channel.position.level},
                          after=[pick_up.id])
            move1 = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": channel.position.x},
                           after=[pick_up.id])

            fork_move = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite),
                               param={"z": channel.capacity - len(channel.items)}, after=[move.id, move1.id])

            drop = Action(r, ActionType.DROP, lambda x: isinstance(x, Satellite), param={"channel_id": channel.id},
                          after=[fork_move.id])
            free = Free(r, lambda x: isinstance(x, Satellite), after=[drop.id])
            free = Free(r, lambda x: isinstance(x, Shuttle), after=[drop.id])
            free = Free(r, lambda x: isinstance(x, Lift), after=[drop.id])
            free = Free(r, lambda x: isinstance(x, Channel), after=[drop.id])

        else:
            block = Block(r, channel.id)
            block1 = Block(r, lambda x: isinstance(x, Satellite) and x.position.section == channel.position.section,
                           after=[block.id])
            block2 = Block(r, lambda x: isinstance(x, Shuttle) and x.position.section == channel.position.section,
                           after=[block1.id])
            block3 = Block(r, lambda x: isinstance(x, Lift) and x.position.section == channel.position.section,
                           after=[block2.id])
            fork_move = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite), param={"z": 0},
                               after=[block.id, block1.id, block2.id, block3.id],
                               condition=lambda x, y: len(sim.find_res_by_id(channel_id, free=False).items) != 0,
                               on_false=Strategy.ab)

            move = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"level": channel.position.level},
                          after=[fork_move.id])
            move1 = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": channel.position.x},
                           after=[fork_move.id])

            fork_move = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite),
                               param={"z": channel.capacity - len(channel.items)},
                               after=[move.id, move1.id])

            pick_up = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Satellite), param={"channel_id": channel_id},
                             after=[move1.id, move.id],
                             condition=lambda x, y: len(sim.find_res_by_id(channel_id, free=False).items) != 0)

            fork_move = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite), param={"z": 0},
                               after=[fork_move.id])

            move = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift),
                          param={"level": Strategy.bay.position.level},
                          after=[fork_move.id])
            move1 = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": 0},
                           after=[fork_move.id])

            drop = Action(r, ActionType.DROP_TO_BAY, lambda x: isinstance(x, Satellite), param={},
                          after=[move1.id, move.id])
            free = Free(r, lambda x: isinstance(x, Satellite), after=[drop.id])
            free = Free(r, lambda x: isinstance(x, Shuttle), after=[drop.id])
            free = Free(r, lambda x: isinstance(x, Lift), after=[drop.id])
            free = Free(r, lambda x: isinstance(x, Channel), after=[drop.id])

        return r

    @staticmethod
    def implement1(task, channel_id, sim, parameter) -> ActionsGraph:
        assert isinstance(task, Task)
        assert isinstance(sim, Simulation)
        assert isinstance(channel_id, int)
        assert isinstance(parameter, SimulationParameter)
        r = ActionsGraph(sim, task)
        channel = sim.find_res_by_id(channel_id)
        lift = sim.find_performer(
            lambda x: isinstance(x, Lift) and x.position.section == channel.position.section, free=False)[0]
        if task.order_type == OrderType.DEPOSIT:
            block_channel = Block(r, channel.id)
            block_sat = Block(r, lambda x: isinstance(x, Satellite) and x.position.section == channel.position.section,
                              after=[block_channel.id])
            block_shu = Block(r, lambda x: isinstance(x, Shuttle) and x.position.section == channel.position.section,
                              after=[block_sat.id], sort_by=lambda x: distance(x.position, Strategy.bay.position,
                                                                               sim.get_status().parameter))
            block_lift = Block(r, lambda x: isinstance(x, Lift) and x.position.section == channel.position.section,
                               after=[block_shu.id])

            branch_shu_lf = Branch(r, after=[block_shu.id],
                                   condition=lambda sim, taken_inf: lift.content is None or lift.content.id != list(
                                       filter(lambda x: isinstance(x, Shuttle), taken_inf))[0].id)

            # go and take shuttle
            fork_move = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite), param={"z": 0},
                               condition=lambda x, y: len(
                                   sim.find_res_by_id(channel_id, free=False).items) != sim.find_res_by_id(channel_id,
                                                                                                           free=False).capacity,
                               after=[block_sat.id, block_shu.id, block_channel.id], branch=branch_shu_lf.id)
            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": 0},
                              after=[fork_move.id], branch=branch_shu_lf.id)

            security_drop = Action(r, ActionType.DROP, lambda x: isinstance(x, Lift),
                                   after=[block_lift.id], branch=branch_shu_lf.id)

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"auto": 0},
                               after=[security_drop.id], branch=branch_shu_lf.id)

            pick_up = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Lift), param={"auto": 0},

                             after=[move_shu.id, move_lift.id], branch=branch_shu_lf.id)

            # go to Strategy.bay and take

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift),
                               param={"level": Strategy.bay.position.level},
                               after=[pick_up.id])

            get = Action(r, ActionType.GET_FROM_BAY, lambda x: isinstance(x, Satellite), param={"item": task.item},

                         after=[move_lift.id])

            # go and deposit

            move = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"level": channel.position.level},
                          after=[get.id])

            drop_shu = Action(r, ActionType.DROP, lambda x: isinstance(x, Lift), after=[move.id])

            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": channel.position.x},
                              after=[drop_shu.id])

            fork_move = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite),
                               param={"z": channel.capacity - len(channel.items)}, after=[move_shu.id])

            drop = Action(r, ActionType.DROP, lambda x: isinstance(x, Satellite), param={"channel_id": channel.id},
                          after=[fork_move.id])
            free = Free(r, lambda x: isinstance(x, Satellite), after=[drop.id])
            free = Free(r, lambda x: isinstance(x, Shuttle), after=[drop.id])
            free = Free(r, lambda x: isinstance(x, Lift), after=[drop_shu.id])
            free = Free(r, lambda x: isinstance(x, Channel), after=[drop.id])

        else:
            block_channel = Block(r, channel.id)
            block_sat = Block(r, lambda x: isinstance(x, Satellite) and x.position.section == channel.position.section,
                              after=[block_channel.id])
            block_shu = Block(r, lambda x: isinstance(x, Shuttle) and x.position.section == channel.position.section,
                              after=[block_sat.id], sort_by=lambda x: distance(x.position, channel.position,
                                                                               sim.get_status().parameter))

            branch_shu_on_level = Branch(r, after=[block_shu.id], condition=lambda sim, taken_inf: list(
                filter(lambda x: isinstance(x, Shuttle), taken_inf))[0].position.level != channel.position.level)

            branch_shu_lf = Branch(r, after=[block_shu.id],
                                   condition=lambda sim, taken_inf: lift.content is None or lift.content.id != list(
                                       filter(lambda x: isinstance(x, Shuttle), taken_inf))[0].id,
                                   branch=branch_shu_on_level)

            # go and take shuttle
            fork_move = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite), param={"z": 0},
                               condition=lambda x, y: len(
                                   sim.find_res_by_id(channel_id, free=False).items) != sim.find_res_by_id(channel_id,
                                                                                                           free=False).capacity,
                               on_false=Strategy.ab,
                               after=[block_sat.id, block_shu.id, block_channel.id], branch=branch_shu_lf.id)
            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": 0},

                              after=[fork_move.id], branch=branch_shu_lf.id)
            block_lift = Block(r, lambda x: isinstance(x, Lift) and x.position.section == channel.position.section,
                               after=[block_shu.id],
                               branch=branch_shu_on_level)

            security_drop = Action(r, ActionType.DROP, lambda x: isinstance(x, Lift),
                                   after=[block_lift.id], branch=branch_shu_lf.id)

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"auto": 0},

                               after=[security_drop.id], branch=branch_shu_lf.id)

            pick_up = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Lift), param={"auto": 0},

                             after=[move_shu.id, move_lift.id], branch=branch_shu_lf.id)
            # go and drop shut to level

            move_l = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"level": channel.position.level},
                            after=[pick_up.id], branch=branch_shu_on_level)

            drop_shu = Action(r, ActionType.DROP, lambda x: isinstance(x, Lift),
                              after=[move_l.id], branch=branch_shu_on_level)

            free_lift = Free(r, lambda x: isinstance(x, Lift), after=[drop_shu.id], branch=branch_shu_on_level)

            # take from channel and return to 0

            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": channel.position.x},
                              after=[drop_shu.id])

            fork_move = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite),
                               param={"z": channel.capacity - len(channel.items)},
                               after=[move_shu.id])

            pick_up = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Satellite), param={"channel_id": channel_id},
                             after=[fork_move.id],
                             condition=lambda x, y: len(sim.find_res_by_id(channel_id, free=False).items) != 0)

            fork_move = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite),
                               param={"z": 0},
                               after=[pick_up.id])

            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": 0},
                              after=[fork_move.id])

            # the lift take shu and return to Strategy.bay

            block_lift = Block(r, lambda x: isinstance(x, Lift) and x.position.section == channel.position.section,
                               after=[pick_up.id])

            security_drop = Action(r, ActionType.DROP, lambda x: isinstance(x, Lift),
                                   after=[block_lift.id])

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"auto": 0},
                               after=[security_drop.id])

            pick_up = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Lift), param={"auto": 0},
                             after=[move_shu.id, move_lift.id])

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift),
                               param={"level": Strategy.bay.position.level},
                               after=[pick_up.id])

            drop = Action(r, ActionType.DROP_TO_BAY, lambda x: isinstance(x, Satellite), param={},
                          after=[move_lift.id])

            free = Free(r, lambda x: isinstance(x, Satellite), after=[drop.id])
            free = Free(r, lambda x: isinstance(x, Shuttle), after=[drop.id])
            free = Free(r, lambda x: isinstance(x, Lift), after=[drop.id])
            free = Free(r, lambda x: isinstance(x, Channel), after=[drop.id])

        return r

    @staticmethod
    def implement2(task, channel_id, sim, parameter) -> ActionsGraph:
        assert isinstance(task, Task)
        assert isinstance(sim, Simulation)
        assert isinstance(channel_id, int)
        assert isinstance(parameter, SimulationParameter)
        r = ActionsGraph(sim, task)
        channel = sim.find_res_by_id(channel_id)
        lift = sim.find_performer(
            lambda x: isinstance(x, Lift) and x.position.section == channel.position.section, free=False)[0]
        if task.order_type == OrderType.DEPOSIT:
            block_channel = Block(r, channel.id)
            block_sat = Block(r, lambda x: isinstance(x, Satellite) and x.position.section == channel.position.section,
                              after=[block_channel.id], sort_by=lambda x: distance(x.position, Strategy.bay.position,
                                                                                   sim.get_status().parameter))
            block_shu = Block(r, lambda x: isinstance(x, Shuttle) and x.position.section == channel.position.section,
                              after=[block_sat.id], sort_by=lambda x: distance(x.position, Strategy.bay.position,
                                                                               sim.get_status().parameter))

            # take sat to 0

            move_sat = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite), param={"z": 0},
                              after=[block_sat.id, block_channel.id], condition=lambda x, y: len(
                    sim.find_res_by_id(channel_id, free=False).items) != sim.find_res_by_id(channel_id,
                                                                                            free=False).capacity,
                              on_false=Strategy.ab)

            # take shuttle to satellite level

            security_drop_shu = Action(r, ActionType.DROP, lambda x: isinstance(x, Shuttle),
                                       after=[block_shu.id, block_sat.id])

            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": 0},
                              after=[security_drop_shu.id])

            # condition check

            branch_sat_shu_lf = Branch(r, after=[block_sat.id, block_shu.id],
                                       condition=lambda sim,
                                                        taken_inf: lift.content is None or lift.content.id !=
                                                                   list(
                                                                       filter(
                                                                           lambda x: isinstance(x, Shuttle),
                                                                           taken_inf))[0].id or list(
                                           filter(lambda x: isinstance(x, Shuttle),
                                                  taken_inf))[0].content is None or list(
                                           filter(lambda x: isinstance(x, Shuttle),
                                                  taken_inf))[0].content != list(
                                           filter(lambda x: isinstance(x, Satellite),
                                                  taken_inf))[0])

            # lift the shu

            block_lift = Block(r, lambda x: isinstance(x, Lift) and x.position.section == channel.position.section,
                               after=[branch_sat_shu_lf.id, block_shu.id],
                               branch=branch_sat_shu_lf)

            security_drop = Action(r, ActionType.DROP, lambda x: isinstance(x, Lift),
                                   after=[block_lift.id, block_shu.id, block_sat.id], branch=branch_sat_shu_lf)

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"auto": 0},

                               after=[security_drop.id, block_shu.id], branch=branch_sat_shu_lf)

            pick_up_shu = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Lift), param={"auto": 0},
                                 after=[move_lift.id, move_shu.id], branch=branch_sat_shu_lf)

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"auto_sat": 0},
                               after=[pick_up_shu.id, block_sat.id], branch=branch_sat_shu_lf)

            drop_shu = Action(r, ActionType.DROP, lambda x: isinstance(x, Lift),
                              after=[move_lift.id], branch=branch_sat_shu_lf)

            free_lift = Free(r, lambda x: isinstance(x, Lift), after=[drop_shu.id], branch=branch_sat_shu_lf)

            # shuttle take sat

            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"auto": 0},
                              after=[drop_shu.id], branch=branch_sat_shu_lf)

            pick_up_sat = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Shuttle), param={"auto": 0},
                                 after=[move_shu.id, move_sat.id], branch=branch_sat_shu_lf)

            # to zero and lift pick_up

            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": 0},
                              after=[pick_up_shu.id, block_shu.id], branch=branch_sat_shu_lf)

            block_lift = Block(r, lambda x: isinstance(x, Lift) and x.position.section == channel.position.section,
                               after=[pick_up_sat.id, free_lift.id])

            security_drop = Action(r, ActionType.DROP, lambda x: isinstance(x, Lift),
                                   after=[block_lift.id], branch=branch_sat_shu_lf)

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"auto": 0},

                               after=[security_drop.id], branch=branch_sat_shu_lf)

            pick_up_shu = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Lift), param={"auto": 0},
                                 after=[move_lift.id, move_shu.id], branch=branch_sat_shu_lf)

            # go to Strategy.bay take and go to level

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift),
                               param={"level": Strategy.bay.position.level},

                               after=[pick_up_shu.id])

            get = Action(r, ActionType.GET_FROM_BAY, lambda x: isinstance(x, Satellite), param={"item": task.item},

                         after=[move_lift.id])

            # go and drop

            move = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"level": channel.position.level},
                          after=[get.id])

            drop_shu = Action(r, ActionType.DROP, lambda x: isinstance(x, Lift), after=[move.id])

            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": channel.position.x},
                              after=[drop_shu.id])

            drop_sat = Action(r, ActionType.DROP, lambda x: isinstance(x, Shuttle), after=[move_shu.id])

            move_sat = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite),
                              param={"z": channel.capacity - len(channel.items)}, after=[drop_sat.id])

            drop = Action(r, ActionType.DROP, lambda x: isinstance(x, Satellite), param={"channel_id": channel.id},
                          after=[move_sat.id])

            free = Free(r, lambda x: isinstance(x, Lift), after=[drop_shu.id])
            free = Free(r, lambda x: isinstance(x, Shuttle), after=[drop_sat.id])
            free = Free(r, lambda x: isinstance(x, Satellite), after=[drop.id])
            free = Free(r, lambda x: isinstance(x, Channel), after=[drop.id])

        else:

            block_channel = Block(r, channel.id)
            block_sat = Block(r, lambda x: isinstance(x, Satellite) and x.position.section == channel.position.section,
                              after=[block_channel.id], sort_by=lambda x: distance(x.position, channel.position,
                                                                                   sim.get_status().parameter))
            block_shu = Block(r, lambda x: isinstance(x, Shuttle) and x.position.section == channel.position.section,
                              after=[block_sat.id], sort_by=lambda x: distance(x.position, channel.position,
                                                                               sim.get_status().parameter))

            # condition check

            branch_sat_shu_lf = Branch(r, after=[block_sat.id, block_shu.id],
                                       condition=lambda sim,
                                                        taken_inf: lift.content is None or lift.content.id !=
                                                                   list(
                                                                       filter(
                                                                           lambda x: isinstance(x, Shuttle),
                                                                           taken_inf))[0].id or list(
                                           filter(lambda x: isinstance(x, Shuttle),
                                                  taken_inf))[0].content is None or list(
                                           filter(lambda x: isinstance(x, Shuttle),
                                                  taken_inf))[0].content != list(
                                           filter(lambda x: isinstance(x, Satellite),
                                                  taken_inf))[0])

            branch_sat_shu_on_level = Branch(r, after=[block_sat.id, block_shu.id, branch_sat_shu_lf.id],
                                             condition=lambda sim,
                                                              taken_inf: list(
                                                 filter(lambda x: isinstance(x, Shuttle),
                                                        taken_inf))[0].position.level != channel.position.level or list(
                                                 filter(lambda x: isinstance(x, Satellite),
                                                        taken_inf))[0].position.level != channel.position.level,
                                             branch=branch_sat_shu_lf.id)

            security_drop_shu = Action(r, ActionType.DROP, lambda x: isinstance(x, Shuttle),
                                       after=[block_shu.id, block_sat.id], branch=branch_sat_shu_lf.id)

            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": 0},
                              after=[security_drop_shu.id], branch=branch_sat_shu_lf.id,
                              condition=lambda x, y: len(sim.find_res_by_id(channel_id, free=False).items) != 0,
                              on_false=Strategy.ab)

            # grab shuttle
            block_lift = Block(r, lambda x: isinstance(x, Lift) and x.position.section == channel.position.section,
                               after=[block_shu.id, branch_sat_shu_on_level.id, block_channel.id],
                               branch=branch_sat_shu_on_level.id)

            security_drop = Action(r, ActionType.DROP, lambda x: isinstance(x, Lift),
                                   after=[block_lift.id, block_shu.id, block_sat.id], branch=branch_sat_shu_on_level.id)

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"auto": 0},

                               after=[security_drop.id, block_shu.id], branch=branch_sat_shu_on_level.id)

            pick_up_shu = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Lift), param={"auto": 0},
                                 after=[move_lift.id, move_shu.id], branch=branch_sat_shu_on_level.id)

            # take shuttle to sat level

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"auto_sat": 0},

                               after=[pick_up_shu.id, block_sat.id], branch=branch_sat_shu_on_level.id)

            drop_shu = Action(r, ActionType.DROP, lambda x: isinstance(x, Lift),

                              after=[move_lift.id], branch=branch_sat_shu_on_level.id)

            free_lift = Free(r, lambda x: isinstance(x, Lift), after=[drop_shu.id], branch=branch_sat_shu_on_level.id)

            # sat to zero

            move_sat = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite), param={"z": 0},
                              after=[block_sat.id, block_channel.id], branch=branch_sat_shu_lf.id)

            # shuttle takes sat and go to x 0 lift grab them

            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"auto": 0},
                              after=[drop_shu.id], branch=branch_sat_shu_lf.id)

            pick_up_sat = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Shuttle), param={"auto": 0},
                                 after=[move_shu.id, move_sat.id], branch=branch_sat_shu_lf.id)

            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": 0},
                              after=[pick_up_shu.id], branch=branch_sat_shu_lf.id)

            block_lift = Block(r, lambda x: isinstance(x, Lift) and x.position.section == channel.position.section,
                               after=[pick_up_sat.id, free_lift.id])

            security_drop = Action(r, ActionType.DROP, lambda x: isinstance(x, Lift),
                                   after=[block_lift.id], branch=branch_sat_shu_lf.id)

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"auto": 0},

                               after=[security_drop.id], branch=branch_sat_shu_lf.id)

            pick_up_shu = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Lift), param={"auto": 0},
                                 after=[move_lift.id, move_shu.id], branch=branch_sat_shu_lf.id)

            # lift take shu and sat to channel level

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift),
                               param={"level": channel.position.level},

                               after=[pick_up_shu.id])

            drop_shu = Action(r, ActionType.DROP, lambda x: isinstance(x, Lift),
                              after=[move_lift.id])

            free_lift = Free(r, lambda x: isinstance(x, Lift), after=[drop_shu.id])

            # retrival

            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": channel.position.x},
                              after=[drop_shu.id])

            drop_sat = Action(r, ActionType.DROP, lambda x: isinstance(x, Shuttle), after=[move_shu.id])

            move_sat = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite),
                              param={"z": channel.capacity - len(channel.items)}, after=[drop_sat.id])

            pick_up = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Satellite), param={"channel_id": channel_id},
                             after=[move_sat.id],
                             condition=lambda x, y: len(sim.find_res_by_id(channel_id, free=False).items) != 0)

            move_sat = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite),
                              param={"z": 0}, after=[pick_up.id])

            pick_up_sat = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Shuttle), param={"auto": 0},
                                 after=[move_sat.id])

            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": 0},
                              after=[pick_up_sat.id])

            block_lift = Block(r, lambda x: isinstance(x, Lift) and x.position.section == channel.position.section,
                               after=[pick_up_sat.id, free_lift.id])

            security_drop = Action(r, ActionType.DROP, lambda x: isinstance(x, Lift),
                                   after=[block_lift.id])

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"auto": 0},

                               after=[security_drop.id])

            pick_up_shu = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Lift), param={"auto": 0},
                                 after=[move_lift.id, move_shu.id])

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift),
                               param={"level": Strategy.bay.position.level},

                               after=[pick_up_shu.id])

            drop = Action(r, ActionType.DROP_TO_BAY, lambda x: isinstance(x, Satellite), param={},
                          after=[move_lift.id])

            # take all to Strategy.bay and finish

            free = Free(r, lambda x: isinstance(x, Satellite), after=[drop.id])
            free = Free(r, lambda x: isinstance(x, Shuttle), after=[drop.id])
            free = Free(r, lambda x: isinstance(x, Lift), after=[drop.id])
            free = Free(r, lambda x: isinstance(x, Channel), after=[pick_up.id])

        return r

    # np.random channel select
    @staticmethod
    def strategy0(task, sim, parameter) -> int:
        assert isinstance(task, Task)
        assert isinstance(parameter, SimulationParameter)
        assert isinstance(sim, Simulation)
        if Strategy.bay is None:
            Strategy.bay = sim.find_res(lambda x: isinstance(x, Bay))[0]
        if task.order_type == OrderType.DEPOSIT:
            # select valid channel
            channels = sim.find_performer(lambda x: isinstance(x, Channel) and len(x.items) < x.capacity and (
                    len(x.items) == 0 or x.items[0].item_type == task.item.item_type))
            if len(channels) == 0:
                sim.logger.log("No place to deposit " + str(task.item), type=sim.Logger.Type.WARNING)
                raise Strategy.NoPlaceTODeposit(task)
            return np.random.choice(channels).id
        elif task.order_type == OrderType.RETRIEVAL:

            channels = sim.find_res(lambda x: isinstance(x, Channel) and
                                              len(x.items) > 0 and x.items[0].item_type == task.item.item_type)
            if len(channels) == 0:
                sim.logger.log("No item to recover " + str(task.item), type=sim.Logger.Type.WARNING)
                raise Strategy.NoItemToTake(task)
            ret = np.random.choice(channels)
            return ret.id

    strategy1_static = None

    # nearest to Strategy.bay
    @staticmethod
    def strategy1(task, sim, parameter) -> int:
        assert isinstance(task, Task)
        assert isinstance(parameter, SimulationParameter)
        assert isinstance(sim, Simulation)

        def w_dist(x, y, par):
            assert isinstance(par, SimulationParameter)
            return abs(x.level - y.level) * par.strategy_par_y * par.Ly + abs(
                x.x - y.x) * par.strategy_par_x * par.Lx

        def init_static():
            Strategy.strategy1_static = sorted([(c, w_dist(c.position, Strategy.bay.position, parameter)) for c in
                                                sim.find_res(lambda x: isinstance(x, Channel), free=False)],
                                               key=lambda x: x[1])

        channels = []

        if Strategy.bay is None:
            Strategy.bay = sim.find_res(lambda x: isinstance(x, Bay))[0]

        if Strategy.strategy1_static is None or sim.now < 100:
            init_static()

        if task.order_type == OrderType.DEPOSIT:
            # select valid channel

            min_dist = 1000000
            for x in Strategy.strategy1_static:
                if x[1] > min_dist:
                    break
                if sim.is_free(x[0]) and len(x[0].items) < x[0].capacity and (
                        len(x[0].items) == 0 or x[0].items[0].item_type == task.item.item_type):
                    min_dist = x[1]
                    channels.append(x[0])

            if len(channels) == 0:
                sim.logger.log("No place to deposit " + str(task.item), type=sim.Logger.Type.WARNING)
                raise Strategy.NoPlaceTODeposit(task, delay=60)


        elif task.order_type == OrderType.RETRIEVAL:

            min_dist = 1000000
            for x in Strategy.strategy1_static:
                if x[1] > min_dist:
                    break
                if sim.is_free(x[0]) and len(x[0].items) > 0 and x[0].items[0].item_type == task.item.item_type:
                    min_dist = x[1]
                    channels.append(x[0])
            if len(channels) == 0:
                sim.logger.log("No item to recover " + str(task.item), type=sim.Logger.Type.WARNING)
                raise Strategy.NoItemToTake(task, delay=60)

        ret = np.random.choice(channels)

        return ret.id

    # nearest to Strategy.bay

    strategy2_static = None

    @staticmethod
    def strategy2(task, sim, parameter) -> int:
        assert isinstance(task, Task)
        assert isinstance(parameter, SimulationParameter)
        assert isinstance(sim, Simulation)

        def w_dist(x, y, par):
            assert isinstance(par, SimulationParameter)
            return abs(x.level - y.level) * par.strategy_par_y * par.Ly + abs(
                x.x - y.x) * par.strategy_par_x * par.Lx

        def dist(channel):
            if channel in Strategy.strategy2_static:
                return Strategy.strategy2_static[channel]
            else:
                a = sorted([(c, w_dist(c.position, channel.position, parameter)) for c in
                            sim.find_res(lambda x: isinstance(x, Channel), free=False)],
                           key=lambda x: x[1])
                Strategy.strategy2_static[channel] = a
                return a

        channels = []

        if Strategy.bay is None:
            Strategy.bay = sim.find_res(lambda x: isinstance(x, Bay))[0]

        if Strategy.strategy2_static is None:
            Strategy.strategy2_static = {}

        if task.order_type == OrderType.DEPOSIT:
            # select valid channel

            # serch for precendent

            center_res = Strategy.bay
            if task.item.item_type in parameter.adjacency:
                for con, list in sorted(parameter.adjacency[task.item.item_type].items(), key=lambda item: item[1]):
                    cha_pre = sim.find_res(
                        lambda c: isinstance(c, Channel) and len(c.items) > 0 and c.items[0].item_type == con,
                        free=False)
                    if len(cha_pre) > 0:
                        center_res = np.random.choice(cha_pre)
                        break

            min_dist = 1000000
            for x in dist(center_res):
                if x[1] > min_dist:
                    break
                if sim.is_free(x[0]) and len(x[0].items) < x[0].capacity and (
                        len(x[0].items) == 0 or x[0].items[0].item_type == task.item.item_type):
                    min_dist = x[1]
                    channels.append(x[0])

            if len(channels) == 0:
                sim.logger.log("No place to deposit " + str(task.item), type=sim.Logger.Type.WARNING)
                raise Strategy.NoPlaceTODeposit(task, delay=60)

        elif task.order_type == OrderType.RETRIEVAL:

            return Strategy.strategy1(task, sim, parameter)

        ret = np.random.choice(channels)

        return ret.id
