from dataclasses import dataclass, field
from collections import deque
from typing import Optional
from enum import Enum, auto

from simos.managers.resource import (
    Resource,
    ResourceManager,
    Printer,
    Sata,
    Scanner,
    Modem,
)
from simos.managers.memory import MemoryManager
from simos.managers.storage import FileManager
from simos.types import Instruction, ScheduleEvent, SystemError, SimulationError


class PCBError(SystemError):
    pass


class SchedulerError(SystemError):
    pass


class State(Enum):
    NEW = auto()
    READY = auto()
    RUNNING = auto()
    BLOCKED = auto()
    TERMINATED = auto()


@dataclass
class CreateFileInstruction(Instruction):
    filename: str
    blocks: int

    def execute(self, process: "PCB", storage: FileManager) -> None:
        try:
            address = storage.create_file(process.pid, self.filename, self.blocks)
            print(
                f"Processo {process.pid} criou arquivo '{self.filename}' no endereço {address}."
            )
        except SystemError as e:
            print(f"Não pode criar arquivo {self.filename}: {e}")


@dataclass
class DeleteFileInstruction(Instruction):
    filename: str

    def execute(self, process: "PCB", storage: FileManager) -> None:
        try:
            storage.delete_file(process.pid, self.filename, process.priority == 0)
            print(f"Processo {process.pid} deletou o arquivo '{self.filename}'.")
        except SystemError as e:
            print(f"Não pode deletar arquivo {self.filename}: {e}")


@dataclass
class PCB:
    pid: int
    priority: int

    # Tempo para ficar pronto logo após ser criado (incialização)
    init_duration: int
    # Tempo que vai ficar na cpu para completar a tarefa
    cpu_duration: int

    # Endereço da memória e espaço alocado (em blocos)
    memory_offset: int
    allocated_blocks: int

    instructions: list[Instruction] = field(default_factory=list)
    last_instruction: int = -1

    use_resources: list[Resource] = field(default_factory=list)
    state: State = State.NEW

    spent_new_time: int = 0
    consumed_cpu_time: int = 0

    arrive_queue_time: Optional[int] = None


class ProcessManager:
    def __init__(
        self, memory: MemoryManager, resource: ResourceManager, storage: FileManager
    ):
        self.memory = memory
        self.resource = resource
        self.storage = storage

        self.process_table: dict[int, PCB] = {}

        self.new_processes: set[int] = set()
        self.blocked_processes: set[int] = set()

        self.realtime_queue: deque[int] = deque()
        self.user_queue: list[deque[int]] = [deque(), deque(), deque()]

        self.terminated: list[int] = []

        self.running: Optional[int] = None
        self.quantum: int = 1  # 1 ms

    def add_process(self, process: PCB):
        """Insere um novo processo na tabela e na fila de \"novos\" """
        self.process_table[process.pid] = process
        self.new_processes.add(process.pid)

    def allocate_memory(self, process: PCB):
        offset = None
        if process.priority == 0:
            offset = self.memory.allocate_real_time(
                process.pid, process.allocated_blocks
            )
        elif process.priority <= 3:
            offset = self.memory.allocate_user(process.pid, process.allocated_blocks)
        else:
            raise PCBError(f"A prioridade {process.priority} não existe.")

        process.memory_offset = offset

    def enqueue_process(self, process: PCB, time: int):
        # Coloca um processo na fila de "ready"
        if process.priority == 0:
            process.arrive_queue_time = time
            self.realtime_queue.append(process.pid)
        elif process.priority <= 3:
            process.arrive_queue_time = time
            self.user_queue[process.priority - 1].append(process.pid)
        else:
            raise SchedulerError(f"A prioridade {process.priority} não existe.")

    def next_process(self):
        self.running = None

        if len(self.realtime_queue) > 0:
            pid = self.realtime_queue.popleft()
            self.running = pid

        for queue in self.user_queue:
            if len(queue) > 0:
                pid = queue.popleft()
                self.running = pid

        if self.running is not None:
            process = self.process_table[pid]
            process.state = State.RUNNING

        return self.running

    def admit_process(self, process: PCB, time: int):
        self.new_processes.remove(process.pid)

        try:
            self.allocate_memory(process)
        except SystemError as e:
            print(f"(time={time}) Processo {process.pid} não pode ser adimitido: {e}")
            process.state = State.TERMINATED
            self.terminated.append(process.pid)
            return

        if len(process.use_resources) > 0:
            if not self.resource.acquire(process.pid, process.use_resources[0]):
                print(
                    f"(time={time}) Bloqueando processo {process.pid}, sem recursos disponíveis."
                )
                process.state = State.BLOCKED
                self.blocked_processes.add(process.pid)
                return

        print(f"(time={time}) Processo {process.pid} pronto.")

        self.enqueue_process(process, time)
        process.state = State.READY

    def unblock_process(self, process: PCB, time: int):
        print(f"(time={time}) Desbloqueando processo {process.pid}.")

        self.blocked_processes.remove(process.pid)
        self.enqueue_process(process, time)
        process.state = State.READY

    def run(self, time: int):
        # Adiciona o tempo gasto pelos processos nas suas filas
        # Isso simula a interrupção de hardware que acontece
        # quando chega um novo processo.
        for pid in list(self.new_processes):
            process = self.process_table[pid]
            if process.spent_new_time >= process.init_duration:
                self.admit_process(process, time)
            else:
                process.spent_new_time += 1

        # Aging: TODO

        # Roda o processo e verifica se ele disparou algum evento
        event = self.run_process(time)
        if event is None:
            return
        elif isinstance(event, ScheduleEvent):
            self.run_scheduler(time)
        else:
            raise ValueError("Evento de sistema não existe.")

    def run_process(self, time: int):
        if self.running is None:
            return ScheduleEvent()

        pid = self.running
        process = self.process_table[pid]

        if 0 <= process.last_instruction + 1 < len(process.instructions):
            process.last_instruction += 1
            print(f"Instrução {process.last_instruction}: ", end="")
            process.instructions[process.last_instruction].execute(
                process, self.storage
            )

        # A cada tick consome um de tempo (para efeitos de simulação)
        process.consumed_cpu_time += 1

        if process.consumed_cpu_time >= process.cpu_duration:
            # Sinalizamos para o escalonador que esse processo
            # terminou
            print(f"(time={time}) Processo {pid} completou.")
            process.state = State.TERMINATED
            return ScheduleEvent()
        elif process.priority > 0 and process.consumed_cpu_time % self.quantum == 0:
            # Sinalizamos para o escalonador que esse processo
            # não foi terminado mas deve ser recolocado na fila
            print(f"(time={time}) Retirando processo {pid}...")
            process.state = State.READY
            return ScheduleEvent()

    def run_scheduler(self, time: int):
        """Escalonador, responsável por fazer troca de contexto."""
        pid = None
        if self.running is None:
            pid = self.next_process()
        else:
            process = self.process_table[self.running]
            if process.state == State.TERMINATED:
                self.terminated.append(self.running)

                self.memory.free(process.memory_offset, process.allocated_blocks)
                if len(process.use_resources) > 0:
                    unblocked_pid = self.resource.release(process.use_resources[0])
                    if unblocked_pid is not None:
                        unblocked_process = self.process_table[unblocked_pid]
                        self.unblock_process(unblocked_process, time)

                pid = self.next_process()
            elif process.state == State.READY:
                self.enqueue_process(process, time)
                pid = self.next_process()
            else:
                raise SimulationError(
                    "Estado inconsistente de processo para fazer troca de contexto."
                )

        if pid is None:
            print(f"(time={time}) Nenhum processo para escalonar.")
        else:
            process = self.process_table[pid]

            printers = process.use_resources.count(lambda r: isinstance(r, Printer))
            scanners = process.use_resources.count(lambda r: isinstance(r, Scanner))
            modems = process.use_resources.count(lambda r: isinstance(r, Modem))
            satas = process.use_resources.count(lambda r: isinstance(r, Sata))

            print("dispatcher => ")
            print(f"    PID: {process.pid}")
            print(f"    offset: {process.memory_offset}")
            print(f"    blocks: {process.allocated_blocks}")
            print(f"    priority: {process.priority}")
            print(f"    time: {time}")
            print(f"    printers: {printers}")
            print(f"    scanners: {scanners}")
            print(f"    modems: {modems}")
            print(f"    satas: {satas}")

            # self.process_table[pid].state = State.RUNNING
            # print(f"(time={time}) Escalonando processo {pid}...")
