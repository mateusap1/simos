from collections import deque
from typing import Optional


class Resource:
    def __init__(self):
        pass


class Printer(Resource):
    def __init__(self, code: int):
        self.code = code

    def __eq__(self, other):
        return isinstance(other, Printer) and other.code == self.code

    def __hash__(self):
        return hash((Printer, self.code))


class Sata(Resource):
    def __init__(self, code: int):
        self.code = code

    def __eq__(self, other):
        return isinstance(other, Sata) and other.code == self.code

    def __hash__(self):
        return hash((Sata, self.code))


class Scanner(Resource):
    def __eq__(self, other):
        return isinstance(other, Scanner)

    def __hash__(self):
        return hash(Scanner)


class Modem(Resource):
    def __eq__(self, other):
        return isinstance(other, Modem)

    def __hash__(self):
        return hash(Modem)


class ResourceManager:
    def __init__(self, available_resources: set[Resource]):
        self.available_resources = available_resources

        # Para cada recurso, fila de PIDs que aguardam
        self.wait_queues: dict[Resource, deque[int]] = {
            r: deque() for r in available_resources
        }

    def acquire(self, pid: int, resource: Resource) -> bool:
        if resource in self.available_resources:
            self.available_resources.remove(resource)
            return True
        
        self.wait_queues[resource].append(pid)
        return False

    def release(self, resource: Resource) -> Optional[int]:
        self.available_resources.add(resource)

        if len(self.wait_queues[resource]) > 0:
            next_pid = self.wait_queues[resource].popleft()
            self.available_resources.remove(resource)
            return next_pid

        return None
