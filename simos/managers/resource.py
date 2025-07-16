from collections import deque
from typing import Optional


class Resource:
    def __init__(self):
        pass


# Cada recurso possui um identificador e comportamento de igualdade/hash próprios
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

        # Uma fila de espera para cada recurso
        self.wait_queues: dict[Resource, deque[int]] = {
            r: deque() for r in available_resources
        }

    def acquire(self, pid: int, resource: Resource) -> bool:
        # Se recurso está disponível, aloca para o processo
        if resource in self.available_resources:
            self.available_resources.remove(resource)
            return True
        
        # Caso contrário, adiciona PID à fila de espera
        self.wait_queues[resource].append(pid)
        return False

    def release(self, resource: Resource) -> Optional[int]:
        # Libera o recurso
        self.available_resources.add(resource)

        # Se houver processos esperando, aloca para o próximo
        if len(self.wait_queues[resource]) > 0:
            next_pid = self.wait_queues[resource].popleft()
            self.available_resources.remove(resource)
            return next_pid

        return None
