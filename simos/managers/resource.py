from collections import deque
from enum import Enum, auto
from typing import Optional


class Resource(Enum):
    PRINTER = auto()
    SCANNER = auto()
    MODEM = auto()
    SATA = auto()


class ResourceManager:
    def __init__(self, available_resources: dict[Resource, int]):
        # Quantos dispositivos de cada tipo temos disponíveis
        self.available_resources = available_resources
        # self.available: dict[Resource, int] = {
        #     Resource.PRINTER: 2,
        #     Resource.SCANNER: 1,
        #     Resource.MODEM: 1,
        #     Resource.SATA: 2,
        # }

        # Para cada recurso, fila de PIDs que aguardam
        self.wait_queues: dict[Resource, deque[int]] = {
            r: deque() for r in self.available_resources
        }

    def acquire(self, pid: int, rtype: Resource) -> bool:
        # Tenta reservar um recurso para pid.
        # Retorna True se conseguiu, False se ficou bloqueado.

        if self.available_resources[rtype] > 0:
            self.available_resources[rtype] -= 1
            return True
        
        # Sem unidades livres: bloqueia o processo
        self.wait_queues[rtype].append(pid)
        return False

    def release(self, pid: int, rtype: Resource) -> Optional[int]:
        # Libera o recurso e passa para o próximo na fila se houver
        self.available_resources[rtype] += 1
        if self.wait_queues[rtype]:
            next_pid = self.wait_queues[rtype].popleft()

            # Reserva esse recurso para o next_pid
            self.available_resources[rtype] -= 1
            return next_pid
        
        return None
