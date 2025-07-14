from collections import deque
from enum import Enum, auto
from typing import List


class Resource:
    def __init__(self):
        pass


class Printer(Resource):
    def __init__(self, code: int):
        self.code = code

    def __eq__(self, other: "Resource"):
        if isinstance(other, Printer):
            return other.code == self.code

        return False


class Sata(Resource):
    def __init__(self, code: int):
        self.code = code

    def __eq__(self, other: "Resource"):
        if isinstance(other, Sata):
            return other.code == self.code

        return False


class Scanner(Resource):
    def __init__(self):
        pass


class Modem(Resource):
    def __init__(self):
        pass


class ResourceManager:
    def __init__(self, available_resources: dict[Resource, int]):
        # Quantos dispositivos de cada tipo temos disponíveis
        self.available_resources: dict[Resource, int] = available_resources

        # Para cada recurso, fila de PIDs que aguardam
        self.wait_queues: dict[Resource, deque[int]] = {
            r: deque() for r in available_resources
        }

        self.waiting_processes: dict[int, set[Resource]] = {}

    def acquire(self, pid: int, resources: List[Resource]):
        remaining_resources: set[Resource] = set()
        for r in resources:
            if self.available_resources.get(r, 0) > 0:
                self.available_resources[r] -= 1
            else:
                # bloqueia pid na fila desse recurso
                self.wait_queues[r].append(pid)
                remaining_resources.add(r)

        self.waiting_processes[pid] = remaining_resources
        if len(remaining_resources) == 0:
            print(f"{len(resources)} recursos obtidos com sucesso.")
        else:
            print(f"{len(resources)} recursos obtidos, esperando liberação dos demais.")

        return len(remaining_resources) == 0

    def release(self, resources: List[Resource]) -> List[int]:
        print(f"Liberando {len(resources)} recursos...")

        awakened: List[int] = []
        for r in resources:
            self.available_resources[r] = self.available_resources.get(r, 0) + 1
            if len(self.wait_queues[r]) == 0:
                continue

            next_pid = self.wait_queues[r].popleft()
            self.available_resources[r] -= 1

            self.waiting_processes[next_pid].remove(r)
            if len(self.waiting_processes[next_pid]) == 0:
                del self.waiting_processes[next_pid]
                awakened.append(next_pid)

        return awakened
