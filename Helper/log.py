import logging
from logging.handlers import RotatingFileHandler
from enum import Enum, unique
from flask import Flask
from os.path import exists, join
from os import makedirs
from .config import Config
import traceback
from typing import Union, Optional, List, Dict, Tuple
from dataclasses import dataclass


class ColoredFormatter(logging.Formatter):
    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)

    RESET_SEQ = '\033[0m'
    COLOR_SEQ = '\033[1;%dm'

    COLORS = {
        'WARNING': YELLOW,
        'INFO': WHITE,
        'DEBUG': BLUE,
        'ERROR': RED,
        'CRITICAL': MAGENTA
    }

    def format(self, record):
        if record.levelname in self.COLORS:
            color_levelname = self.COLOR_SEQ \
                              % (30 + self.COLORS[record.levelname]) \
                              + record.levelname \
                              + self.RESET_SEQ
            record.levelname = color_levelname
        return logging.Formatter.format(self, record)


@unique
class Level(Enum):
    DEBUG, INFO, WARNING, ERROR, CRITICAL = range(5)


@dataclass
class LogInfo:
    Log: List[Tuple[str, str]] = None
    Count: Dict[str, int] = None

    def __init__(self, dictionary):
        self.Log = dictionary["Log"]
        self.Count = dictionary["Count"]

    @staticmethod
    def FromLog(log: List[str]):
        def _inferLevel(line:str) -> str:
            if ' - CRITICAL - ' in line: return 'Critical'
            if ' - ERROR - ' in line: return 'Error'
            if ' - WARNING - ' in line: return 'Warning'
            if ' - INFO - ' in line: return 'Info'
            return 'Debug'

        res = LogInfo()
        for line in log:
            level = _inferLevel(line)
            res.Count[level] += 1
            res.Log.append((level, line))
        return res

    def Serialize(self) -> Dict:
        return {
            "Count": self.Count,
            "Log": self.Log
        }


class Log:
    CONSOLE_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
    FILE_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

    # Rotating log files configuration
    LOG_SIZE = 16777216
    LOG_COUNT = 10

    initialized = False
    app: Flask = None

    @classmethod
    def Initialize(cls, app: Flask):
        config = Config()
        folder = config.Logging.Folder

        if not exists(folder): makedirs(folder)

        # Accept all messages on Flask logger, but display only up to the selected level
        app.logger.setLevel(logging.DEBUG)
        console_handler: logging.StreamHandler = app.logger.handlers[0]
        console_handler.setLevel(config.Logging.AppLevel)
        console_handler.setFormatter(ColoredFormatter(cls.CONSOLE_FORMAT))

        # Attach new file handler
        file_handler = RotatingFileHandler(
            join(folder, 'Scheduler.log'), maxBytes=cls.LOG_SIZE, backupCount=cls.LOG_COUNT)
        file_handler.setFormatter(logging.Formatter(cls.FILE_FORMAT))
        file_handler.setLevel(config.Logging.LogLevel)
        app.logger.addHandler(file_handler)

        # Put console logger at the end (to avoid saving _colors_ to file)
        app.logger.handlers.reverse()

        cls.app = app
        cls.initialized = True

    @classmethod
    def _dump(cls, level: str, msg: str, logger: Optional[str] = None):
        if cls.initialized:
            log = cls.app.logger if logger is None else logging.getLogger(logger)
            method = getattr(log, level.lower())
            method(msg)
        else:
            print(f"[Log not initialized][{level}] {msg}")

    @classmethod
    def D(cls, msg, logger: Optional[str] = None): cls._dump('DEBUG', msg, logger)

    @classmethod
    def I(cls, msg, logger: Optional[str] = None): cls._dump('INFO', msg, logger)

    @classmethod
    def W(cls, msg, logger: Optional[str] = None): cls._dump('WARNING', msg, logger)

    @classmethod
    def E(cls, msg, logger: Optional[str] = None): cls._dump('ERROR', msg, logger)

    @classmethod
    def C(cls, msg, logger: Optional[str] = None): cls._dump('CRITICAL', msg, logger)

    @staticmethod
    def State(condition: bool) -> str:
        return f'{"En" if condition else "Dis"}abled'

    @classmethod
    def Log(cls, level: Union[Level, str], msg: str, logger: Optional[str] = None):
        if isinstance(level, str):
            level = Level[level]

        if level == Level.DEBUG: cls.D(msg, logger)
        if level == Level.INFO: cls.I(msg, logger)
        if level == Level.WARNING: cls.W(msg, logger)
        if level == Level.ERROR: cls.E(msg, logger)
        if level == Level.CRITICAL: cls.C(msg, logger)

    @classmethod
    def Traceback(cls, info):
        exc_type, exc_value, exc_traceback = info
        lines = traceback.format_exception(exc_type, exc_value, exc_traceback, limit=2)
        for line in lines:
            cls.D(line.strip())

    @classmethod
    def OpenLogFile(cls, identifier: str, filePath: Optional[str] = None) -> str:
        filePath = join(Config().Logging.Folder, f'{identifier}.log') if filePath is None else filePath

        logger = logging.getLogger(identifier)
        logger.setLevel(logging.DEBUG)

        fileHandler = logging.FileHandler(filename=filePath, mode='a+', encoding='utf-8')
        fileHandler.setFormatter(logging.Formatter(cls.FILE_FORMAT))
        fileHandler.setLevel(logging.DEBUG)

        logger.addHandler(fileHandler)
        Log.D('[File Opened]', identifier)
        return filePath

    @classmethod
    def CloseLogFile(cls, identifier):
        Log.D('[Closing File]', identifier)
        logger = logging.getLogger(identifier)
        for handler in logger.handlers:  # type: logging.Handler
            logger.removeHandler(handler)
            handler.flush()
            handler.close()

    @classmethod
    def RetrieveLog(cls, file: str = None, tail: Optional[int] = None) -> List[str]:
        res = []
        file = join(Config().Logging.Folder, 'Scheduler.log') if file is None else file
        with open(file, 'r', encoding='utf-8') as log:
            for l in log: res.append(l)
        if tail is not None and tail < len(res):
            start = len(res) - tail
            return res[start:len(res)]
        return res

    @classmethod
    def RetrieveLogInfo(cls, file:str = None, tail: Optional[int] = None) -> LogInfo:
        log = cls.RetrieveLog(file, tail)
        return LogInfo.FromLog(log)
