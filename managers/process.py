from dataclasses import dataclass
from collections import deque
from enum import Enum

import time


class SchedulerError(Exception):
    pass


class State(Enum):
    NEW = 0
    READY = 1
    RUNNING = 2
    BLOCKED = 3
    TERMINATED = 4


@dataclass
class PCB:
    pid: int
    state: State

    priority: int
    arrive_time: float
    dispatch_time: float  # for quantum
    complete_time: float

    memory_offset: int
    memory_alloc: int

    use_printer: bool
    use_scanner: bool
    use_drivers: bool

    def is_complete(self):
        return time.time() > self.complete_time

    def quantum_expired(self, quantum: int):
        # TODO: Verificar isso, porque aqui ele não conta o tempo da CPU,
        # mas conta o tempo total, então conta também o tempo do escalonador
        duration = (time.time() - self.dispatch_time) / 1000
        return duration >= quantum


class ProcessManager:
    def __init__(self, processes: dict[int, PCB]):
        self.process_table: dict[int, PCB] = processes

        self.new_queue: deque[int] = deque()
        self.blocked_queue: deque[int] = deque()

        self.realtime_queue: deque[int] = deque()
        self.user_queue: list[deque[int]] = [deque(), deque(), deque()]

        self.terminated: list[int] = []

        self.running: int = None
        self.quantum = 1  # ms

    def insert(self, process: PCB):
        """Insere um novo processo na tabela e na fila de \"novos\" """
        self.process_table[process.pid] = process
        self.new_queue.append(process.pid)

    def enqueue_process(self, pid: int):
        """Coloca um processo na fila de \"ready\" """
        process = self.process_table[pid]
        if process.state != State.READY:
            raise SchedulerError(
                f"Não é possível enfilerar um processo com estado {process.state}"
            )

        if process.priority == 0:
            self.realtime_queue.append(pid)
        elif process.priority <= 3:
            self.user_queue[process.priority - 1] = pid
        else:
            raise SchedulerError(f"A prioridade {process.priority} não existe.")

    def next_process(self):
        if len(self.realtime_queue) > 0:
            pid = self.realtime_queue.popleft()
            self.running = pid
            return self.running

        for queue in self.user_queue:
            if len(queue) > 0:
                pid = queue.popleft()
                self.running = pid
                return self.running

    def scheduler(self, is_quantum: bool):
        """ Escalonador, responsável por fazer troca de contexto.
            Assume-se que o escalonador vai ser chamado todo quantum ou
            quando chegar um novo processo por exemplo. Isso é deteminado
            pela flag `is_quantum`.
        """

        # Novos processos
        while len(self.new_queue) > 0:
            pid = self.new_queue.popleft()
            self.enqueue_process(pid)

        # Verificar se processo terminou
        if self.running is not None:
            pid = self.running
            process = self.process_table[pid]

        # Aging

        # Escalonador
        if self.running is None:
            self.next_process()
        else:
            process = self.process_table[self.running]
            if process.quantum_expired(self.quantum):
                self.enqueue_process(self.running)
                self.next_process()
            elif process.is_complete():
                self.terminated.append(self.running)
                self.next_process()

    # def arrive(self, id: int):
    #     self.new_queue.put(pid)

    # def start(self, pid: int):
