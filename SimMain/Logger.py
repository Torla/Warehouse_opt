from enum import Enum


class Logger:
    env = None
    enabled = True

    class Type(Enum):
        NORMAL = ""
        HEADER = '\033[95m'
        BLUE = '\033[94m'
        WARNING = '\033[93m'
        GREEN = '\033[92m'
        FAIL = '\033[91m'
        UNDERLINE = '\033[4m'

    @staticmethod
    def set_env(env):
        Logger.env = env

    @staticmethod
    def enable(value):
        Logger.enabled = value

    @staticmethod
    def log(msg, indent=0, type=Type.NORMAL):
        if not Logger.enabled:
            return
        s = str(Logger.env.now) + ":" + " " * indent + msg
        print(type.value + s + '\033[0m')
