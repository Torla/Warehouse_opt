from Manager.Action import Action
from SimMain import Logger


class Performer:
    def __init__(self, env, id):
        self.id = id
        self.env = env

    class IllegalAction(Exception):
        def __init__(self, msg):
            self.msg = msg

    def perform(self, action, taken_inf, all_resources):
        assert isinstance(action, Action)
        Logger.Logger.log(str(self) + " performing " + str(action.actionType) + " par: " + str(action.param), 10)
