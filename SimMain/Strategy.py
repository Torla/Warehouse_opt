from IdeaSim.Event import Event
from IdeaSim.Actions import ActionsGraph, Action, Block, Free
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
                               condition=lambda x: len(
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
                               condition=lambda x: len(sim.find_res_by_id(channel_id, free=False).items) != 0,
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
                             condition=lambda x: len(sim.find_res_by_id(channel_id, free=False).items) != 0)

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
    def implement1(task, channel_id, resources, all_resources, parameter) -> ActionsGraph:
        assert isinstance(task, Task)
        assert isinstance(resources, Resources)
        assert isinstance(channel_id, int)
        assert isinstance(parameter, SimulationParameter)
        r = ActionsGraph({}, [])
        channels = list(filter(lambda x: isinstance(x, Channel), all_resources))
        channel = list(filter(lambda x: x.id == channel_id, channels))[0]
        bay = list(filter(lambda x: isinstance(x, Bay), all_resources))[0]
        if isinstance(channel.lift.content, Shuttle) and channel.lift.content in resources.items:
            shuttle = channel.lift.content
        else:
            shuttles = list(filter(lambda x: isinstance(x, Shuttle) and x.position.section == channel.position.section,
                                   resources.items))
            # lift can be not free at the moment of scheduling
            if len(shuttles) == 0:
                raise Strategy.NeedToWait(task)
            else:
                # select nearest to channel
                shuttles.sort(key=lambda x: distance(x.position, channel.position, parameter))
                shuttle = shuttles[0]

        satellite = list(filter(lambda x: isinstance(x, Satellite) and x.position.section == channel.position.section,
                                resources.items))
        if len(satellite) == 0:
            raise Strategy.NeedToWait(task)
        else:
            satellite = satellite[0]

        if task.order_type == OrderType.DEPOSIT:
            # block all except lift
            r.tasks.append(task)
            block = Action(ActionType.BLOCK, channel_id)
            r.actions[block.id] = block
            block2 = Action(ActionType.BLOCK, shuttle.id)
            r.actions[block2.id] = block2
            block3 = Action(ActionType.BLOCK, satellite.id)
            r.actions[block3.id] = block3

            move = Action(ActionType.MOVE, satellite.id, {"z": 0},
                          [block.id, block2.id, block3.id])
            r.actions[move.id] = move

            action = Action(ActionType.MOVE, shuttle.id, {"x": 0},
                            [move.id])
            r.actions[action.id] = action

            # move lift to level of shuttle
            block_lift = Action(ActionType.BLOCK, channel.lift.id, {}, [])
            r.actions[block_lift.id] = block_lift
            # todo manage when lift contains shuttle
            lift_move = Action(ActionType.DROP, channel.lift.id, {},
                               [block_lift.id])
            r.actions[lift_move.id] = lift_move
            lift_move = Action(ActionType.MOVE, channel.lift.id, {"resource": shuttle.id},
                               [lift_move.id])
            r.actions[lift_move.id] = lift_move
            # pick up shuttle
            pick_up = Action(ActionType.PICKUP, channel.lift.id, {"shuttle": shuttle.id},
                             [lift_move.id, action.id])
            r.actions[pick_up.id] = pick_up

            # move lift to bay
            lift_move = Action(ActionType.MOVE, channel.lift.id, {"level": parameter.bay_level},
                               [pick_up.id])
            r.actions[lift_move.id] = lift_move

            # get from bay
            block_bay = Action(ActionType.BLOCK, bay.id, {}, [lift_move.id])
            r.actions[block_bay.id] = block_bay
            get = Action(ActionType.GET_FROM_BAY, satellite.id, {"level": parameter.bay_level, "item": task.item},
                         [block_bay.id])
            r.actions[get.id] = get
            free_bay = Action(ActionType.FREE, bay.id, {}, [get.id])
            r.actions[free_bay.id] = free_bay

            # move lift to level and drop shuttle
            lift_move = Action(ActionType.MOVE, channel.lift.id, {"level": channel.position.level},
                               [get.id])
            r.actions[lift_move.id] = lift_move

            lift_drop = Action(ActionType.DROP, channel.lift.id, {}, [lift_move.id])
            r.actions[lift_drop.id] = lift_drop

            shuttle_move = Action(ActionType.MOVE, shuttle.id, {"x": channel.position.x},
                                  [lift_drop.id])
            r.actions[shuttle_move.id] = shuttle_move

            # move satellite to channel and drop (fork)
            fork_move = Action(ActionType.MOVE, satellite.id, {"z": channel.first_item_z_position()},
                               [shuttle_move.id])
            r.actions[fork_move.id] = fork_move
            drop = Action(ActionType.DROP, satellite.id, {"channel_id": channel.id},
                          [fork_move.id])
            r.actions[drop.id] = drop

            # free all
            # lift is free after his last drop
            action = Action(ActionType.FREE, channel.lift.id, after=[lift_drop.id])
            r.actions[action.id] = action
            action = Action(ActionType.FREE, channel_id, after=[drop.id])
            r.actions[action.id] = action
            action = Action(ActionType.FREE, satellite.id, after=[drop.id])
            r.actions[action.id] = action
            action = Action(ActionType.FREE, shuttle.id, after=[drop.id])
            r.actions[action.id] = action

        elif task.order_type == OrderType.RETRIEVAL:
            # block all
            r.tasks.append(task)
            block = Action(ActionType.BLOCK, channel_id)
            r.actions[block.id] = block

            block2 = Action(ActionType.BLOCK, shuttle.id)
            r.actions[block2.id] = block2
            block3 = Action(ActionType.BLOCK, satellite.id)
            r.actions[block3.id] = block3

            # if the shuttle is not in the right level
            action = None
            if shuttle.position.level != channel.position.level:
                # lift is blocked separately after the others resources to have parallelism
                block_lift = Action(ActionType.BLOCK, channel.lift.id, {}, [block.id, block2.id, block3.id])
                r.actions[block_lift.id] = block_lift

                # move satellite to shuttle (retract fork)
                move = Action(ActionType.MOVE, satellite.id, {"z": 0},
                              [block.id, block2.id, block3.id])
                r.actions[move.id] = move

                # move shuttle to 0
                move = Action(ActionType.MOVE, shuttle.id, {"x": 0},
                              [move.id])
                r.actions[move.id] = move

                # move lift , pick up shuttle and move to destination
                # todo consider deadlock

                fake_drop = Action(ActionType.DROP, channel.lift.id, {}, [block_lift.id])
                r.actions[fake_drop.id] = fake_drop

                action1 = Action(ActionType.MOVE, channel.lift.id, {"resource": shuttle.id},
                                 [fake_drop.id])
                r.actions[action1.id] = action1

                pick_up = Action(ActionType.PICKUP, channel.lift.id, {"shuttle": shuttle.id},
                                 [move.id, action1.id])
                r.actions[pick_up.id] = pick_up

                action1 = Action(ActionType.MOVE, channel.lift.id, {"level": channel.position.level},
                                 [pick_up.id])
                r.actions[action1.id] = action1

                # drop shuttle

                drop = Action(ActionType.DROP, channel.lift.id, {},
                              [action1.id])
                r.actions[drop.id] = drop

                action = Action(ActionType.FREE, channel.lift.id, after=[drop.id])
                r.actions[action.id] = action

                # move shuttle,extend fork and  get
                action = Action(ActionType.MOVE, shuttle.id, {"x": channel.position.x},
                                [drop.id])
                r.actions[action.id] = action
            else:
                # retract fork and move shuttle (same but as first after block)
                move = Action(ActionType.MOVE, satellite.id, {"z": 0},
                              [block.id, block2.id, block3.id])
                r.actions[move.id] = move

                action = Action(ActionType.MOVE, shuttle.id, {"x": channel.position.x},
                                [move.id])
                r.actions[action.id] = action

            action1 = Action(ActionType.MOVE, satellite.id, {"z": channel.first_item_z_position()},
                             [action.id])
            r.actions[action1.id] = action1

            # get and retract

            pick_up = Action(ActionType.PICKUP, satellite.id, {"channel_id": channel.id}, [action.id])
            r.actions[pick_up.id] = pick_up
            fork_move = Action(ActionType.MOVE, satellite.id, {"z": 0},
                               [pick_up.id])
            r.actions[fork_move.id] = fork_move

            # move shuttle to 0 and pickup by lift
            action = Action(ActionType.MOVE, shuttle.id, {"x": 0},
                            [fork_move.id])
            r.actions[action.id] = action

            # lift is blocked separately after the others resources to have parallelism
            block_lift = Action(ActionType.BLOCK, channel.lift.id, {}, [block.id, block2.id, block3.id])
            r.actions[block_lift.id] = block_lift

            fake_drop = Action(ActionType.DROP, channel.lift.id, {}, [block_lift.id])
            r.actions[fake_drop.id] = fake_drop

            move = Action(ActionType.MOVE, channel.lift.id, {"resource": shuttle.id}, [fake_drop.id])
            r.actions[move.id] = move

            pick_up = Action(ActionType.PICKUP, channel.lift.id, {"shuttle": shuttle.id},
                             [action.id, move.id])
            r.actions[pick_up.id] = pick_up

            # move to bay

            action1 = Action(ActionType.MOVE, channel.lift.id, {"level": parameter.bay_level},
                             [pick_up.id])
            r.actions[action1.id] = action1

            # drop to bay
            block_bay = Action(ActionType.BLOCK, bay.id, {}, [action1.id])
            r.actions[block_bay.id] = block_bay

            drop = Action(ActionType.DROP_TO_BAY, satellite.id, {}, [block_bay.id])
            r.actions[drop.id] = drop

            free_bay = Action(ActionType.FREE, bay.id, {}, [drop.id])
            r.actions[free_bay.id] = free_bay

            # free all
            action = Action(ActionType.FREE, channel.lift.id, after=[drop.id])
            r.actions[action.id] = action
            action = Action(ActionType.FREE, channel_id, after=[drop.id])
            r.actions[action.id] = action
            action = Action(ActionType.FREE, satellite.id, after=[drop.id])
            r.actions[action.id] = action
            action = Action(ActionType.FREE, shuttle.id, after=[drop.id])
            r.actions[action.id] = action

        return r

    @staticmethod
    def implement2(task, channel_id, resources, all_resources, parameter) -> ActionsGraph:
        assert isinstance(task, Task)
        assert isinstance(resources, Resources)
        assert isinstance(channel_id, int)
        assert isinstance(parameter, SimulationParameter)
        r = ActionsGraph({}, [])
        channels = list(filter(lambda x: isinstance(x, Channel), all_resources))
        channel = list(filter(lambda x: x.id == channel_id, channels))[0]
        bay = list(filter(lambda x: isinstance(x, Bay), all_resources))[0]

        # clean is when no waiting is needed for resources
        clean_shuttle = False
        clean_lift = False

        if isinstance(channel.lift.content, Shuttle) \
                and channel.lift.content in resources.items and channel.lift in resources.items:
            shuttle = channel.lift.content
            clean_shuttle = True
            clean_lift = True
        else:
            shuttles = list(filter(lambda x: isinstance(x, Shuttle) and x.position.section == channel.position.section,
                                   resources.items))
            if len(shuttles) != 0:
                clean_shuttle = True
            else:
                shuttles = list(
                    filter(lambda x: isinstance(x, Shuttle) and x.position.section == channel.position.section,
                           all_resources))
                # shuttle can be not free at the moment of scheduling
                # select nearest to channel
            shuttles.sort(key=lambda x: distance(x.position, channel.position, parameter))
            shuttle = shuttles[0]

        if isinstance(shuttle.content, Satellite) and shuttle.content in resources.items:
            satellite = shuttle.content
        else:
            satellites = list(
                filter(lambda x: isinstance(x, Satellite) and x.position.section == channel.position.section,
                       resources.items))
            # lift can be not free at the moment of scheduling
            if len(satellites) == 0:
                raise Strategy.NeedToWait(task)
            else:
                # select nearest to channel
                satellites.sort(key=lambda x: distance(x.position, channel.position, parameter))
                satellite = satellites[0]

        if task.order_type == OrderType.DEPOSIT:

            r.tasks.append(task)
            block_channel = Action(ActionType.BLOCK, channel_id)
            r.actions[block_channel.id] = block_channel
            block_sat = Action(ActionType.BLOCK, satellite.id)
            r.actions[block_sat.id] = block_sat

            action = None
            if shuttle.content == satellite and channel.lift.content == shuttle and clean_lift and clean_shuttle:
                # todo to test many of this
                block_shuttle = Action(ActionType.BLOCK, shuttle.id, {}, [block_channel.id, block_sat.id])
                r.actions[block_shuttle.id] = block_shuttle

                action = Action(ActionType.BLOCK, channel.lift.id, {}, [block_shuttle.id])
                r.actions[action.id] = action
            elif shuttle.content != satellite and channel.lift.content == shuttle and clean_lift and clean_shuttle:
                # move satellite to center
                move_sat = Action(ActionType.MOVE, satellite.id, {"z": 0},
                                  [block_sat.id, block_channel.id])
                r.actions[move_sat.id] = move_sat

                # take shuttle to satellite level

                block_shuttle = Action(ActionType.BLOCK, shuttle.id, {}, [block_sat.id, block_channel.id])
                r.actions[block_shuttle.id] = block_shuttle

                block_lift = Action(ActionType.BLOCK, channel.lift.id, {}, [block_shuttle.id])
                r.actions[block_lift.id] = block_lift

                move = Action(ActionType.MOVE, channel.lift.id, {"resource": satellite.id},
                              [block_lift.id])
                r.actions[move.id] = move

                drop = Action(ActionType.DROP, channel.lift.id, {}, [move.id])
                r.actions[drop.id] = drop

                free_lift = Action(ActionType.FREE, channel.lift.id, {}, [drop.id])
                r.actions[free_lift.id] = free_lift

                # shuttle pick up satellite and move to x:0
                fake_drop = Action(ActionType.DROP, shuttle.id, {}, [drop.id])
                r.actions[fake_drop.id] = fake_drop

                move = Action(ActionType.MOVE, shuttle.id, {"resource": satellite.id}, [drop.id])
                r.actions[move.id] = move

                pick_up_satellite = Action(ActionType.PICKUP, shuttle.id, {"satellite": satellite.id},
                                           [move.id, move_sat.id])
                r.actions[pick_up_satellite.id] = pick_up_satellite

                move_shuttle = Action(ActionType.MOVE, shuttle.id, {"x": 0}, [pick_up_satellite.id])
                r.actions[move_shuttle.id] = move_shuttle

                # pick up by lift

                block_lift = Action(ActionType.BLOCK, channel.lift.id, {}, [free_lift.id])
                r.actions[block_lift.id] = block_lift

                fake_drop = Action(ActionType.DROP, channel.lift.id, {}, [block_lift.id])
                r.actions[fake_drop.id] = fake_drop

                move = Action(ActionType.MOVE, channel.lift.id, {"resource": shuttle.id},
                              [fake_drop.id])
                r.actions[move.id] = move

                action = Action(ActionType.PICKUP, channel.lift.id, {"shuttle": shuttle.id},
                                [move.id, move_shuttle.id])
                r.actions[action.id] = action
            elif shuttle.content == satellite and channel.lift.content != shuttle and clean_shuttle:

                # move shuttle to x:0

                block_shuttle = Action(ActionType.BLOCK, shuttle.id, {}, [block_channel.id, block_sat.id])
                r.actions[block_shuttle.id] = block_shuttle

                move_shuttle = Action(ActionType.MOVE, shuttle.id, {"x": 0}, [block_shuttle.id])
                r.actions[move_shuttle.id] = move_shuttle

                # pick up by lift

                block_lift = Action(ActionType.BLOCK, channel.lift.id, {}, [block_shuttle.id])
                r.actions[block_lift.id] = block_lift

                fake_drop = Action(ActionType.DROP, channel.lift.id, {}, [block_lift.id])
                r.actions[fake_drop.id] = fake_drop

                move = Action(ActionType.MOVE, channel.lift.id, {"resource": shuttle.id},
                              [fake_drop.id])
                r.actions[move.id] = move

                action = Action(ActionType.PICKUP, channel.lift.id, {"shuttle": shuttle.id},
                                [move.id, move_shuttle.id])
                r.actions[action.id] = action
            elif shuttle.content != satellite and channel.lift.content != shuttle \
                    and shuttle.position.level == satellite.position.level and clean_shuttle:
                # move satellite to center
                move_sat = Action(ActionType.MOVE, satellite.id, {"z": 0},
                                  [block_sat.id, block_channel.id])
                r.actions[move_sat.id] = move_sat

                # shuttle pick up satellite and move to x:0

                block_shuttle = Action(ActionType.BLOCK, shuttle.id)
                r.actions[block_shuttle.id] = block_shuttle

                move = Action(ActionType.MOVE, shuttle.id, {"resource": satellite.id}, [move_sat.id, block_shuttle.id])
                r.actions[move.id] = move

                pick_up_satellite = Action(ActionType.PICKUP, shuttle.id, {"satellite": satellite.id},
                                           [move.id, move_sat.id])
                r.actions[pick_up_satellite.id] = pick_up_satellite

                move_shuttle = Action(ActionType.MOVE, shuttle.id, {"x": 0}, [pick_up_satellite.id])
                r.actions[move_shuttle.id] = move_shuttle

                # pick up by lift

                block_lift = Action(ActionType.BLOCK, channel.lift.id, {}, [block_shuttle.id])
                r.actions[block_lift.id] = block_lift

                fake_drop = Action(ActionType.DROP, channel.lift.id, {}, [block_lift.id])
                r.actions[fake_drop.id] = fake_drop

                move = Action(ActionType.MOVE, channel.lift.id, {"resource": shuttle.id},
                              [fake_drop.id])
                r.actions[move.id] = move

                action = Action(ActionType.PICKUP, channel.lift.id, {"shuttle": shuttle.id},
                                [move.id, move_shuttle.id])
                r.actions[action.id] = action
            elif shuttle.content != satellite and channel.lift.content != shuttle \
                    and shuttle.position.level != satellite.position.level or not clean_shuttle:
                # move satellite to center
                move_sat = Action(ActionType.MOVE, satellite.id, {"z": 0},
                                  [block_sat.id, block_channel.id])
                r.actions[move_sat.id] = move_sat

                # take shuttle to satellite level

                block_shuttle = Action(ActionType.BLOCK, shuttle.id, {}, [block_sat.id, block_channel.id])
                r.actions[block_shuttle.id] = block_shuttle

                fake_drop = Action(ActionType.DROP, shuttle.id, {}, [block_shuttle.id])
                r.actions[fake_drop.id] = fake_drop

                move_shuttle = Action(ActionType.MOVE, shuttle.id, {"x": 0},
                                      [fake_drop.id])
                r.actions[move_shuttle.id] = move_shuttle

                block_lift = Action(ActionType.BLOCK, channel.lift.id, {}, [block_shuttle.id])
                r.actions[block_lift.id] = block_lift

                fake_drop = Action(ActionType.DROP, channel.lift.id, {}, [block_lift.id])
                r.actions[fake_drop.id] = fake_drop

                move = Action(ActionType.MOVE, channel.lift.id, {"resource": shuttle.id},
                              [fake_drop.id])
                r.actions[move.id] = move

                pick_up_shuttle = Action(ActionType.PICKUP, channel.lift.id, {"shuttle": shuttle.id},
                                         [move.id, move_shuttle.id])
                r.actions[pick_up_shuttle.id] = pick_up_shuttle

                move = Action(ActionType.MOVE, channel.lift.id, {"resource": satellite.id},
                              [pick_up_shuttle.id])
                r.actions[move.id] = move

                drop = Action(ActionType.DROP, channel.lift.id, {}, [move.id])
                r.actions[drop.id] = drop

                free_lift = Action(ActionType.FREE, channel.lift.id, {}, [drop.id])
                r.actions[free_lift.id] = free_lift

                # shuttle pick up satellite and move to x:0
                move = Action(ActionType.MOVE, shuttle.id, {"resource": satellite.id}, [drop.id])
                r.actions[move.id] = move

                pick_up_satellite = Action(ActionType.PICKUP, shuttle.id, {"satellite": satellite.id},
                                           [move.id, move_sat.id])
                r.actions[pick_up_satellite.id] = pick_up_satellite

                move_shuttle = Action(ActionType.MOVE, shuttle.id, {"x": 0}, [pick_up_satellite.id])
                r.actions[move_shuttle.id] = move_shuttle

                # pick up by lift

                block_lift = Action(ActionType.BLOCK, channel.lift.id, {}, [free_lift.id])
                r.actions[block_lift.id] = block_lift

                fake_drop = Action(ActionType.DROP, channel.lift.id, {}, [block_lift.id])
                r.actions[fake_drop.id] = fake_drop

                move = Action(ActionType.MOVE, channel.lift.id, {"resource": shuttle.id},
                              [fake_drop.id])
                r.actions[move.id] = move

                action = Action(ActionType.PICKUP, channel.lift.id, {"shuttle": shuttle.id},
                                [move.id, move_shuttle.id])
                r.actions[action.id] = action

            # move to bay and take item

            move = Action(ActionType.MOVE, channel.lift.id, {"level": bay.position.level},
                          [action.id])
            r.actions[move.id] = move

            block_bay = Action(ActionType.BLOCK, bay.id, {}, [move.id])
            r.actions[block_bay.id] = block_bay

            get = Action(ActionType.GET_FROM_BAY, satellite.id, {"item": task.item}, [block_bay.id])
            r.actions[get.id] = get

            free_bay = Action(ActionType.FREE, bay.id, {}, [get.id])
            r.actions[free_bay.id] = free_bay

            # move to channel and drop sequence

            move = Action(ActionType.MOVE, channel.lift.id, {"level": channel.position.level},
                          [get.id])
            r.actions[move.id] = move

            drop = Action(ActionType.DROP, channel.lift.id, {}, [move.id])
            r.actions[drop.id] = drop

            action = Action(ActionType.FREE, channel.lift.id, after=[drop.id])
            r.actions[action.id] = action

            move = Action(ActionType.MOVE, shuttle.id, {"x": channel.position.x},
                          [drop.id])
            r.actions[move.id] = move

            drop = Action(ActionType.DROP, shuttle.id, {}, [move.id])
            r.actions[drop.id] = drop

            action = Action(ActionType.FREE, shuttle.id, after=[drop.id])
            r.actions[action.id] = action

            move = Action(ActionType.MOVE, satellite.id, {"z": channel.first_item_z_position()},
                          [drop.id])
            r.actions[move.id] = move

            last_drop = Action(ActionType.DROP, satellite.id, {"channel_id": channel.id}, [move.id])
            r.actions[last_drop.id] = last_drop

            # free all
            # lift and shuttle are  free after their last drop

            action = Action(ActionType.FREE, satellite.id, after=[last_drop.id])
            r.actions[action.id] = action
            action = Action(ActionType.FREE, channel_id, after=[last_drop.id])
            r.actions[action.id] = action

        elif task.order_type == OrderType.RETRIEVAL:

            r.tasks.append(task)
            block_channel = Action(ActionType.BLOCK, channel_id)
            r.actions[block_channel.id] = block_channel
            block_sat = Action(ActionType.BLOCK, satellite.id)
            r.actions[block_sat.id] = block_sat

            action = None

            # todo free shuttle when satellite is dropping

            if channel.lift.content == shuttle and shuttle.content == satellite and clean_shuttle and clean_lift:
                # go to level and drop shuttle
                block_shuttle = Action(ActionType.BLOCK, shuttle.id, {}, [block_sat.id, block_channel.id])
                r.actions[block_shuttle.id] = block_shuttle

                block_lift = Action(ActionType.BLOCK, channel.lift.id, {}, [block_shuttle.id])
                r.actions[block_lift.id] = block_lift

                move_lift = Action(ActionType.MOVE, channel.lift.id, {"level": channel.position.level},
                                   [block_lift.id])
                r.actions[move_lift.id] = move_lift

                drop = Action(ActionType.DROP, channel.lift.id, {}, [move_lift.id])
                r.actions[drop.id] = drop

                free_lift = Action(ActionType.FREE, channel.lift.id, after=[drop.id])
                r.actions[free_lift.id] = free_lift

                # go and drop satellite in the channel

                move_shuttle = Action(ActionType.MOVE, shuttle.id, {"x": channel.position.x}, [drop.id])
                r.actions[move_shuttle.id] = move_shuttle

                drop = Action(ActionType.DROP, shuttle.id, {}, [move_shuttle.id])
                r.actions[drop.id] = drop

                action = drop
            # elif channel.lift.content == shuttle and shuttle.content != satellite and clean_shuttle and clean_lift:
            # elif channel.lift.content != shuttle and shuttle.content == satellite and channel.position.level == shuttle.position.level and clean_shuttle:
            # elif channel.lift.content != shuttle and shuttle.content == satellite and channel.position.level != shuttle.position.level and clean_shuttle:
            # elif channel.position.level == satellite.position.level and channel.position.x == satellite.position.x and channel.position.level == shuttle.position.level and clean_shuttle:
            # elif channel.position.level == satellite.position.level and channel.position.x == satellite.position.x and channel.position.level != shuttle.position.level:
            # elif channel.position.level == satellite.position.level and channel.position.x != satellite.position.x and channel.position.level == shuttle.position.level and clean_shuttle:
            # elif channel.position.level == satellite.position.level and channel.position.x != satellite.position.x and channel.position.level != shuttle.position.level:
            else:
                # take shuttle to satellite level
                block_shuttle = Action(ActionType.BLOCK, shuttle.id, {}, [block_sat.id, block_channel.id])
                r.actions[block_shuttle.id] = block_shuttle

                drop = Action(ActionType.DROP, shuttle.id, {}, [block_shuttle.id])
                r.actions[drop.id] = drop

                move_shuttle = Action(ActionType.MOVE, shuttle.id, {"x": 0}, [drop.id])
                r.actions[move_shuttle.id] = move_shuttle

                block_lift = Action(ActionType.BLOCK, channel.lift.id, {}, [block_shuttle.id])
                r.actions[block_lift.id] = block_lift

                drop = Action(ActionType.DROP, channel.lift.id, {}, [block_lift.id])
                r.actions[drop.id] = drop

                move_lift = Action(ActionType.MOVE, channel.lift.id, {"resource": shuttle.id}, [drop.id])
                r.actions[move_lift.id] = move_lift

                pick_up_shuttle = Action(ActionType.PICKUP, channel.lift.id, {"shuttle": shuttle.id},
                                         [move_shuttle.id, move_lift.id])
                r.actions[pick_up_shuttle.id] = pick_up_shuttle

                move_lift = Action(ActionType.MOVE, channel.lift.id, {"resource": satellite.id}, [pick_up_shuttle.id])
                r.actions[move_lift.id] = move_lift

                drop = Action(ActionType.DROP, channel.lift.id, {}, [move_lift.id])
                r.actions[drop.id] = drop

                free_lift = Action(ActionType.FREE, channel.lift.id, after=[drop.id])
                r.actions[free_lift.id] = free_lift

                # shuttle go and take satellite and return to border
                move_sat = Action(ActionType.MOVE, satellite.id, {"z": 0}, [block_sat.id])
                r.actions[move_sat.id] = move_sat

                move_shuttle = Action(ActionType.MOVE, shuttle.id, {"resource": satellite.id}, [drop.id])
                r.actions[move_shuttle.id] = move_shuttle

                pick_up_sat = Action(ActionType.PICKUP, shuttle.id, {"satellite": satellite.id},
                                     [move_shuttle.id, move_sat.id])
                r.actions[pick_up_sat.id] = pick_up_sat

                move_shuttle = Action(ActionType.MOVE, shuttle.id, {"x": 0}, [pick_up_sat.id])
                r.actions[move_shuttle.id] = move_shuttle

                # lift take shuttle containing the satellite to te channel level

                block_lift = Action(ActionType.BLOCK, channel.lift.id, {}, [free_lift.id])
                r.actions[block_lift.id] = block_lift

                drop = Action(ActionType.DROP, channel.lift.id, {}, [block_lift.id])
                r.actions[drop.id] = drop

                move_lift = Action(ActionType.MOVE, channel.lift.id, {"resource": shuttle.id}, [drop.id])
                r.actions[move_lift.id] = move_lift

                pick_up_shuttle = Action(ActionType.PICKUP, channel.lift.id, {"shuttle": shuttle.id},
                                         [move_shuttle.id, move_lift.id])
                r.actions[pick_up_shuttle.id] = pick_up_shuttle

                move_lift = Action(ActionType.MOVE, channel.lift.id, {"level": channel.position.level},
                                   [pick_up_shuttle.id])
                r.actions[move_lift.id] = move_lift

                drop = Action(ActionType.DROP, channel.lift.id, {}, [move_lift.id])
                r.actions[drop.id] = drop

                free_lift = Action(ActionType.FREE, channel.lift.id, after=[drop.id])
                r.actions[free_lift.id] = free_lift

                # go and drop satellite in the channel

                move_shuttle = Action(ActionType.MOVE, shuttle.id, {"x": channel.position.x}, [drop.id])
                r.actions[move_shuttle.id] = move_shuttle

                drop = Action(ActionType.DROP, shuttle.id, {}, [move_shuttle.id])
                r.actions[drop.id] = drop

                action = drop

            # drop item and return to x:0

            move_sat = Action(ActionType.MOVE, satellite.id, {"z": channel.first_item_z_position()}, [action.id])
            r.actions[move_sat.id] = move_sat

            get = Action(ActionType.PICKUP, satellite.id, {"channel_id": channel_id}, [move_sat.id])
            r.actions[get.id] = get

            move_sat = Action(ActionType.MOVE, satellite.id, {"z": 0}, [get.id])
            r.actions[move_sat.id] = move_sat

            pick_up_sat = Action(ActionType.PICKUP, shuttle.id, {"satellite": satellite.id},
                                 [move_sat.id])
            r.actions[pick_up_sat.id] = pick_up_sat

            move_shuttle = Action(ActionType.MOVE, shuttle.id, {"x": 0}, [pick_up_sat.id])
            r.actions[move_shuttle.id] = move_shuttle

            # take all to bay

            block_lift = Action(ActionType.BLOCK, channel.lift.id, {}, [action.id])
            r.actions[block_lift.id] = block_lift

            drop = Action(ActionType.DROP, channel.lift.id, {}, [block_lift.id])
            r.actions[drop.id] = drop

            move_lift = Action(ActionType.MOVE, channel.lift.id, {"resource": shuttle.id}, [drop.id])
            r.actions[move_lift.id] = move_lift

            pick_up_shuttle = Action(ActionType.PICKUP, channel.lift.id, {"shuttle": shuttle.id},
                                     [move_shuttle.id, move_lift.id])
            r.actions[pick_up_shuttle.id] = pick_up_shuttle

            move_lift = Action(ActionType.MOVE, channel.lift.id, {"level": bay.position.level}, [pick_up_shuttle.id])
            r.actions[move_lift.id] = move_lift

            block_bay = Action(ActionType.BLOCK, bay.id, {}, [move_lift.id])
            r.actions[block_bay.id] = block_bay

            drop = Action(ActionType.DROP_TO_BAY, satellite.id, {}, [block_bay.id])
            r.actions[drop.id] = drop

            free_bay = Action(ActionType.FREE, bay.id, {}, [drop.id])
            r.actions[free_bay.id] = free_bay

            # free all
            action = Action(ActionType.FREE, channel.lift.id, after=[drop.id])
            r.actions[action.id] = action
            action = Action(ActionType.FREE, channel_id, after=[drop.id])
            r.actions[action.id] = action
            action = Action(ActionType.FREE, satellite.id, after=[drop.id])
            r.actions[action.id] = action
            action = Action(ActionType.FREE, shuttle.id, after=[drop.id])
            r.actions[action.id] = action

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
