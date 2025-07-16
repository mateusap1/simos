from dataclasses import dataclass
from simos.types import SystemError


# Erros personalizados para diferentes falhas do sistema de arquivos
class OutOfStorageError(SystemError):
    pass


class FilePermissionError(SystemError):
    pass


class FileNotExistError(SystemError):
    pass


@dataclass
class Metadata:
    name: str
    owner: int
    address: int
    size: int


class FileManager:
    def __init__(self, disk_size: int, initial_files: list[tuple[str, int, int]]):
        # Inicializa os blocos do disco
        self.blocks: list[str] = [None for _ in range(disk_size)]
        self.metadata: dict[str, Metadata] = {}

        # Pela especificação não está claro o processo dono
        # dos arquivos iniciais. Assumiremos que somente
        # processos em tempo real possam deletá-los.

        # Arquivos iniciais são atribuídos ao "dono" -1 (tempo real)
        for filename, address, size in initial_files:
            file = Metadata(name=filename, owner=-1, address=address, size=size)
            self.metadata[filename] = file

            # Marca os blocos como ocupados pelo arquivo
            for i in range(address, address + size):
                self.blocks[i] = filename

    def create_file(self, pid: str, filename: str, size: int):
        # Busca espaço contíguo disponível
        address = self.first_fit(size)
        if address is None:
            raise OutOfStorageError(f"Sem espaço livre para criar arquivo {filename}.")

        # Cria metadados e marca os blocos
        file = Metadata(name=filename, owner=pid, address=address, size=size)
        self.metadata[filename] = file

        for i in range(address, address + size):
            self.blocks[i] = filename

        return address

    def delete_file(self, pid: int, name: str, is_real_time: bool = False):
        file = self.metadata.get(name)
        if file is None:
            raise FileNotExistError(f"Arquivo {name} não existe.")

        # Somente o dono ou um processo de tempo real pode deletar
        if not is_real_time and file.owner != pid:
            raise FilePermissionError(
                f"Processo {pid} não tem permissão para deletar arquivo {name}."
            )

        # Libera os blocos e remove metadados
        for i in range(file.address, file.address + file.size):
            self.blocks[i] = None

        del self.metadata[name]

    def first_fit(self, size: int):
        # Busca o primeiro espaço contíguo livre com tamanho suficiente
        count = 0
        for i in range(len(self.blocks)):
            if self.blocks[i] is None:
                count += 1
                if count == size:
                    return i - size + 1
            else:
                count = 0

        return None
