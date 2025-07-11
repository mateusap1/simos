from dataclasses import dataclass
from enum import Enum


class ResourceType(Enum):
    SCANNER = 0
    PRINTER = 0
    MODEM = 0
    SATA = 0


@dataclass
class Resource:
    code: str
    type: ResourceType