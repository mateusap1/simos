from simos.types import SystemError

class OutOfMemoryError(SystemError):
    pass


class MemoryManager:
    def __init__(self):
        self.memory = [None for _ in range(1024)]

    def allocate_real_time(self, label: str, space: int):
        offset = self.find_fit(space, 0, 64)
        if offset is None:
            raise OutOfMemoryError(f"Memória insuficiente para processo {label} em tempo real.")

        self.allocate(label, offset, space)

        return offset

    def allocate_user(self, label: str, space: int):
        offset = self.find_fit(space, 64, 1024)
        if offset is None:
            raise OutOfMemoryError(f"Memória insuficiente para processo {label} de usuário.")

        self.allocate(label, offset, space)

        return offset
    
    def allocate(self, label: str, offset: int, space: int):
        for i in range(offset, offset+space):
            self.memory[i] = label

        print(f"Processo {label} alocou {space} blocos com sucesso em {offset}.")

    def free(self, offset: int, space: int):
        for i in range(offset, offset+space):
            self.memory[i] = None

        print(f"{space} blocos liberados com sucesso em {offset}.")

    def find_fit(self, size: int, start: int, end: int):
        count = 0
        for i in range(start, end):
            if self.memory[i] is None:
                count += 1
                if count == size:
                    return i - size + 1
            else:
                count = 0
                
        return None