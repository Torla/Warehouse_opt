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
from SimMain.Logger import Logger
from SimMain.SimulationParameter import SimulationParameter
from Task.Task import Task, OrderType
from IdeaSim.Simulation import Simulation
from IdeaSim.Manager import Manager
import numpy as np
import random


# first number:
#   0 -> only lift
#   1 -> lift + shuttle
#   2 -> all
# second number strategy

class Strategy:
    class NoPlaceTODeposit(Manager.RetryLater):
        def __init__(self, task):
            self.task = task

    class NoItemToTake(Manager.RetryLater):
        def __init__(self, task):
            self.task = task

    class NeedToWait(Manager.RetryLater):
        def __init__(self, task):
            self.task = task

    @staticmethod
    def select_type(l, tipe):
        return list(filter(lambda x: isinstance(x, tipe), l))[0]

    @staticmethod
    def strategy(event) -> ActionsGraph:
        assert isinstance(event, Event)
        event.sim.logger.log(
            "New task dispached " + str(event.param["task"].order_type) + " " + str(event.param["task"].item))
        parameter = event.sim.get_status().parameter
        try:
            selection = Strategy.__dict__["strategy" + str(parameter.tech) + str(parameter.strategy)] \
                .__func__(event.param["task"], event.sim, parameter)
        except KeyError:
            Logger.log("Strategy or technology selected is not defined", type=Logger.Type.FAIL)
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
            Logger.log("Technology selected is not defined", type=Logger.Type.FAIL)
            exit(-1)

    @staticmethod
    def ab(action, sim):
        assert (isinstance(sim, Simulation))
        sim.logger.log("aborting " + str(action), type=sim.Logger.Type.WARNING)
        Action.abort(action, sim)

    @staticmethod
    def implement0(task, channel_id, sim, parameter) -> ActionsGraph:
        assert isinstance(task, Task)
        assert isinstance(sim, Simulation)
        assert isinstance(channel_id, int)
        assert isinstance(parameter, SimulationParameter)
        r = ActionsGraph(sim)
        channel = sim.find_res_by_id(channel_id)
        bay = sim.find_res(lambda x: isinstance(x, Bay))[0]
        if task.order_type == OrderType.DEPOSIT:
            block3 = Block(r, channel.id)
            block = Block(r, lambda x: isinstance(x, Lift) and x.position.section == channel.position.section)
            block1 = Block(r, lambda x: isinstance(x, Shuttle) and x.position.section == channel.position.section)
            block2 = Block(r, lambda x: isinstance(x, Satellite) and x.position.section == channel.position.section)
            fork_move = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite), param={"z": 0},
                               condition=lambda x, y: len(
                                   sim.find_res_by_id(channel_id, free=False).items) != sim.find_res_by_id(channel_id,
                                                                                                           free=False).capacity,
                               after=[block.id, block1.id, block2.id, block3.id])
            move = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"level": bay.position.level},
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
            block3 = Block(r, channel.id)
            block = Block(r, lambda x: isinstance(x, Lift) and x.position.section == channel.position.section)
            block1 = Block(r, lambda x: isinstance(x, Shuttle) and x.position.section == channel.position.section)
            block2 = Block(r, lambda x: isinstance(x, Satellite) and x.position.section == channel.position.section)
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

            move = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"level": bay.position.level},
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
        r = ActionsGraph(sim)
        channel = sim.find_res_by_id(channel_id)
        bay = sim.find_res(lambda x: isinstance(x, Bay))[0]
        lift = sim.find_res(
            lambda x: isinstance(x, Lift) and x.position.section == channel.position.section, free=False)[0]
        if task.order_type == OrderType.DEPOSIT:
            block_channel = Block(r, channel.id)
            block_sat = Block(r, lambda x: isinstance(x, Satellite) and x.position.section == channel.position.section)
            block_shu = Block(r, lambda x: isinstance(x, Shuttle) and x.position.section == channel.position.section)
            block_lift = Block(r, lambda x: isinstance(x, Lift) and x.position.section == channel.position.section)

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

            # go to bay and take

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"level": bay.position.level},
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
            block_sat = Block(r, lambda x: isinstance(x, Satellite) and x.position.section == channel.position.section)
            block_shu = Block(r, lambda x: isinstance(x, Shuttle) and x.position.section == channel.position.section)

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
                               after=[block_sat.id, block_shu.id, block_channel.id], branch=branch_shu_lf.id)
            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": 0},

                              after=[fork_move.id], branch=branch_shu_lf.id)
            block_lift = Block(r, lambda x: isinstance(x, Lift) and x.position.section == channel.position.section,
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

            # the lift take shu and return to bay

            block_lift = Block(r, lambda x: isinstance(x, Lift) and x.position.section == channel.position.section,
                               after=[pick_up.id])

            security_drop = Action(r, ActionType.DROP, lambda x: isinstance(x, Lift),
                                   after=[block_lift.id])

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"auto": 0},
                               after=[security_drop.id])

            pick_up = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Lift), param={"auto": 0},
                             after=[move_shu.id, move_lift.id])

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"level": bay.position.level},
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
        r = ActionsGraph(sim)
        channel = sim.find_res_by_id(channel_id)
        bay = sim.find_res(lambda x: isinstance(x, Bay))[0]
        lift = sim.find_res(
            lambda x: isinstance(x, Lift) and x.position.section == channel.position.section, free=False)[0]
        if task.order_type == OrderType.DEPOSIT:
            block_channel = Block(r, channel.id)
            block_sat = Block(r, lambda x: isinstance(x, Satellite) and x.position.section == channel.position.section)
            block_shu = Block(r, lambda x: isinstance(x, Shuttle) and x.position.section == channel.position.section)
            block_lift = Block(r, lambda x: isinstance(x, Lift) and x.position.section == channel.position.section)

            # take sat to 0

            move_sat = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite), param={"z": 0},
                              after=[block_sat.id, block_channel.id])

            # take shuttle to satellite level

            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": 0},
                              after=[block_shu.id])

            security_drop = Action(r, ActionType.DROP, lambda x: isinstance(x, Lift),
                                   after=[block_lift.id])

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"auto": 0},

                               after=[security_drop.id,block_shu.id])

            pick_up_shu = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Lift), param={"auto": 0},
                                 after=[move_lift.id, move_shu.id])

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"auto_sat": 0},
                               after=[pick_up_shu.id,block_sat.id])

            drop_shu = Action(r, ActionType.DROP, lambda x: isinstance(x, Lift),
                              after=[move_lift.id])

            free_lift = Free(r, lambda x: isinstance(x, Lift), after=[drop_shu.id])

            # shuttle take sat

            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"auto": 0},
                              after=[drop_shu.id])

            pick_up_sat = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Shuttle), param={"auto": 0},
                                 after=[move_shu.id, move_sat.id])

            # to zero and lift pick_up

            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": 0},
                              after=[pick_up_shu.id, block_shu.id])

            block_lift = Block(r, lambda x: isinstance(x, Lift) and x.position.section == channel.position.section,
                               after=[pick_up_sat.id, free_lift.id])

            security_drop = Action(r, ActionType.DROP, lambda x: isinstance(x, Lift),
                                   after=[block_lift.id])

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"auto": 0},

                               after=[security_drop.id])

            pick_up_shu = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Lift), param={"auto": 0},
                                 after=[move_lift.id, move_shu.id])

            # go to bay take and go to level

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"level": bay.position.level},

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
            block_sat = Block(r, lambda x: isinstance(x, Satellite) and x.position.section == channel.position.section)
            block_shu = Block(r, lambda x: isinstance(x, Shuttle) and x.position.section == channel.position.section)

            branch_shu_on_level = Branch(r, after=[block_shu.id], condition=lambda sim, taken_inf: list(
                filter(lambda x: isinstance(x, Shuttle), taken_inf))[0].position.level != channel.position.level)

            branch_shu_lf = Branch(r, after=[block_shu.id],
                                   condition=lambda sim, taken_inf: lift.content is None or lift.content.id != list(
                                       filter(lambda x: isinstance(x, Shuttle), taken_inf))[0].id,
                                   branch=branch_shu_on_level)

            # go and take shuttle
            move_sat = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite), param={"z": 0},
                              condition=lambda x, y: len(
                                  sim.find_res_by_id(channel_id, free=False).items) != sim.find_res_by_id(channel_id,
                                                                                                          free=False).capacity,
                              after=[block_sat.id, block_shu.id, block_channel.id], branch=branch_shu_lf.id)
            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": 0},

                              after=[move_sat.id], branch=branch_shu_lf.id)
            block_lift = Block(r, lambda x: isinstance(x, Lift) and x.position.section == channel.position.section,
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

            move_sat = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite),
                              param={"z": channel.capacity - len(channel.items)},
                              after=[move_shu.id])

            pick_up = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Satellite), param={"channel_id": channel_id},
                             after=[move_sat.id],
                             condition=lambda x, y: len(sim.find_res_by_id(channel_id, free=False).items) != 0)

            move_sat = Action(r, ActionType.MOVE, lambda x: isinstance(x, Satellite),
                              param={"z": 0},
                              after=[pick_up.id])

            move_shu = Action(r, ActionType.MOVE, lambda x: isinstance(x, Shuttle), param={"x": 0},
                              after=[move_sat.id])

            # the lift take shu and return to bay

            block_lift = Block(r, lambda x: isinstance(x, Lift) and x.position.section == channel.position.section,
                               after=[pick_up.id])

            security_drop = Action(r, ActionType.DROP, lambda x: isinstance(x, Lift),
                                   after=[block_lift.id])

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"auto": 0},
                               after=[security_drop.id])

            pick_up = Action(r, ActionType.PICKUP, lambda x: isinstance(x, Lift), param={"auto": 0},
                             after=[move_shu.id, move_lift.id])

            move_lift = Action(r, ActionType.MOVE, lambda x: isinstance(x, Lift), param={"level": bay.position.level},
                               after=[pick_up.id])

            drop = Action(r, ActionType.DROP_TO_BAY, lambda x: isinstance(x, Satellite), param={},
                          after=[move_lift.id])

            free = Free(r, lambda x: isinstance(x, Satellite), after=[drop.id])
            free = Free(r, lambda x: isinstance(x, Shuttle), after=[drop.id])
            free = Free(r, lambda x: isinstance(x, Lift), after=[drop.id])
            free = Free(r, lambda x: isinstance(x, Channel), after=[drop.id])

        return r

    # random channel select
    @staticmethod
    def strategy00(task, sim, parameter) -> int:
        assert isinstance(task, Task)
        assert isinstance(parameter, SimulationParameter)
        assert isinstance(sim, Simulation)
        if task.order_type == OrderType.DEPOSIT:
            # select valid channel
            channels = sim.find_res(lambda x: isinstance(x, Channel) and len(x.items) < x.capacity and (
                    len(x.items) == 0 or x.items[0].item_type == task.item.item_type))
            if len(channels) == 0:
                sim.logger.log("No place to deposit " + str(task.item), type=Logger.Type.WARNING)
                raise Strategy.NoPlaceTODeposit(task)
            return random.choice(channels).id
        elif task.order_type == OrderType.RETRIEVAL:

            channels = sim.find_res(lambda x: isinstance(x, Channel) and
                                              len(x.items) > 0 and x.items[0].item_type == task.item.item_type)
            if len(channels) == 0:
                sim.logger.log("No item to recover " + str(task.item), type=Logger.Type.WARNING)
                raise Strategy.NoItemToTake(task)
            ret = random.choice(channels)
            return ret.id

    @staticmethod
    def strategy10(task, sim, parameter) -> int:
        assert isinstance(task, Task)
        assert isinstance(parameter, SimulationParameter)
        assert isinstance(sim, Simulation)
        if task.order_type == OrderType.DEPOSIT:
            # select valid channel
            channels = sim.find_res(lambda x: isinstance(x, Channel) and len(x.items) < x.capacity and (
                    len(x.items) == 0 or x.items[0].item_type == task.item.item_type))
            if len(channels) == 0:
                sim.logger.log("No place to deposit " + str(task.item), type=Logger.Type.WARNING)
                raise Strategy.NoPlaceTODeposit(task)
            return random.choice(channels).id
        elif task.order_type == OrderType.RETRIEVAL:

            channels = sim.find_res(lambda x: isinstance(x, Channel) and
                                              len(x.items) > 0 and x.items[0].item_type == task.item.item_type)
            if len(channels) == 0:
                sim.logger.log("No item to recover " + str(task.item), type=Logger.Type.WARNING)
                raise Strategy.NoItemToTake(task)
            ret = random.choice(channels)
            return ret.id

    @staticmethod
    def strategy20(task, sim, parameter) -> int:
        assert isinstance(task, Task)
        assert isinstance(parameter, SimulationParameter)
        assert isinstance(sim, Simulation)
        if task.order_type == OrderType.DEPOSIT:
            # select valid channel
            channels = sim.find_res(lambda x: isinstance(x, Channel) and len(x.items) < x.capacity and (
                    len(x.items) == 0 or x.items[0].item_type == task.item.item_type))
            if len(channels) == 0:
                sim.logger.log("No place to deposit " + str(task.item), type=Logger.Type.WARNING)
                raise Strategy.NoPlaceTODeposit(task)
            return random.choice(channels).id
        elif task.order_type == OrderType.RETRIEVAL:

            channels = sim.find_res(lambda x: isinstance(x, Channel) and
                                              len(x.items) > 0 and x.items[0].item_type == task.item.item_type)
            if len(channels) == 0:
                sim.logger.log("No item to recover " + str(task.item), type=Logger.Type.WARNING)
                raise Strategy.NoItemToTake(task)
            ret = random.choice(channels)
            return ret.id

    # nearest to bay
    @staticmethod
    def strategy01(task, sim, parameter) -> int:
        assert isinstance(task, Task)
        assert isinstance(parameter, SimulationParameter)
        assert isinstance(sim, Simulation)
        if task.order_type == OrderType.DEPOSIT:
            # select valid channel
            channels = sim.find_res(lambda x: isinstance(x, Channel) and len(x.items) < x.capacity and (
                    len(x.items) == 0 or x.items[0].item_type == task.item.item_type))
            if len(channels) == 0:
                sim.logger.log("No place to deposit " + str(task.item), type=Logger.Type.WARNING)
                raise Strategy.NoPlaceTODeposit(task)
            return random.choice(channels).id
        elif task.order_type == OrderType.RETRIEVAL:

            channels = sim.find_res(lambda x: isinstance(x, Channel) and
                                              len(x.items) > 0 and x.items[0].item_type == task.item.item_type)
            if len(channels) == 0:
                sim.logger.log("No item to recover " + str(task.item), type=Logger.Type.WARNING)
                raise Strategy.NoItemToTake(task)
            bays = sim.find_res(func=lambda x: isinstance(x, Bay), free=False)
            bay_pos = bays[0].position
            ret = sorted(channels, key=lambda x: distance(x.position, bay_pos, sim.get_status().parameter))[0]
            return ret.id
