from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class LogInfo:
    Log: List[Tuple[str, str]] = None
    Count: Dict[str, int] = None

    def __init__(self, dictionary):
        self.Log = dictionary["Log"]
        self.Count = dictionary["Count"]
