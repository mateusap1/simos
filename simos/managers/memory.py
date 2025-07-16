from collections import deque
from simos.types import SystemError

# Erro personalizado para falta de memória
class OutOfMemoryError(SystemError):
    pass


class MemoryManager:
    def __init__(self):
        # Inicializa 1024 blocos de memória como livres (None)
        self.memory = [None for _ in range(1024)]
        self.waiting_queue: deque[tuple[int, int, bool]] = deque()

    def allocate_real_time(self, pid: int, space: int):
        # Tenta alocar nos primeiros 64 blocos (tempo real)
        offset = self.find_fit(space, 0, 64)
        if offset is None:
            self.waiting_queue.append((pid, space, True))
            raise OutOfMemoryError(f"Memória insuficiente para processo {pid} em tempo real.")

        self.allocate(pid, offset, space)
        return offset

    def allocate_user(self, pid: int, space: int):
        # Tenta alocar nos blocos 64 a 1023 (usuário)
        offset = self.find_fit(space, 64, 1024)
        if offset is None:
            self.waiting_queue.append((pid, space, False))
            raise OutOfMemoryError(f"Memória insuficiente para processo {pid} de usuário.")

        self.allocate(pid, offset, space)
        return offset
    
    def allocate(self, pid: int, offset: int, space: int):
        # Marca os blocos como ocupados pelo processo
        for i in range(offset, offset+space):
            self.memory[i] = pid

    def free(self, offset: int, space: int) -> list[int]:
        # Libera os blocos ocupados a partir de um offset
        for i in range(offset, offset+space):
            self.memory[i] = None

        unblocked: list[int] = []
        while len(self.waiting_queue) > 0:
            pid, size, is_realtime = self.waiting_queue.popleft()
            start, end = (0, 64) if is_realtime else (64, 1024)
            address = self.find_fit(size, start, end)
            if address is None:
                return unblocked
            else:
                self.allocate(pid, address, space)
                unblocked.append(pid)

        return unblocked
        

    def find_fit(self, size: int, start: int, end: int):
        # Busca um espaço contíguo livre entre os índices [start, end)
        count = 0
        for i in range(start, end):
            if self.memory[i] is None:
                count += 1
                if count == size:
                    return i - size + 1
            else:
                count = 0

        return None
