import argparse


from simos.managers.process import (
    PCB,
    CreateFileInstruction,
    DeleteFileInstruction,
    ProcessManager,
    MemoryManager,
    ResourceManager,
)
from simos.managers.resource import Printer, Scanner, Sata, Modem, Resource
from simos.managers.storage import FileManager


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("process_file", help="Arquivo de processos")
    parser.add_argument("ops_file", help="Arquivo de operações")
    args = parser.parse_args()

    # Lê processos
    processes: dict[int, PCB] = {}
    resources: set[Resource] = set()
    with open(args.process_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            init, prio, cpu, blocks, prn, scn, modem, disk = parts
            pid = len(processes)
            pcb = PCB(
                pid=pid,
                priority=int(prio),
                init_duration=int(init),
                cpu_duration=int(cpu),
                memory_offset=0,
                allocated_blocks=int(blocks),
            )

            # Não ficou claro na especificação

            # Assumimos que 0 é um código "morto" e implica a não
            # utilização da impressora ou do Sata, isso é inferido
            # pelos exemplos aprensentados

            # Caso contrário, o código será aquilo que estiver nessa
            # coluna
            if prn != "0":
                pcb.use_resources.append(Printer(prn))
            if scn == "1":
                pcb.use_resources.append(Scanner())
            if modem == "1":
                pcb.use_resources.append(Modem())
            if disk != "0":
                pcb.use_resources.append(Sata(disk))

            if len(pcb.use_resources) > 0:
                resources.add(pcb.use_resources[0])

            if len(pcb.use_resources) > 1:
                raise ValueError("Cada processo deve utilizar um recurso somente.")

            processes[pid] = pcb

    # Lê operações de arquivos
    with open(args.ops_file) as f:
        total_blocks = int(f.readline().strip())
        n_segments = int(f.readline().strip())

        initial_files: list[tuple[str, int, int]] = []
        for _ in range(n_segments):
            line = f.readline().strip()
            filename, address, size = [p.strip() for p in line.split(",")]
            initial_files.append((filename, int(address), int(size)))

        for line in f:
            line = line.strip()
            if not line:
                continue
            pid_str, op_code, filename, *rest = [p.strip() for p in line.split(",")]
            pid = int(pid_str)
            if op_code == "0":
                blocks_n = int(rest[0])
                instr = CreateFileInstruction(filename, blocks_n)
            else:
                instr = DeleteFileInstruction(filename)
            if pid in processes:
                processes[pid].instructions.append(instr)
            else:
                print(f"Processo {pid} não existe")

    mm = MemoryManager()
    rm = ResourceManager(resources)
    sm = FileManager(total_blocks, initial_files)
    pm = ProcessManager(mm, rm, sm)
    for pcb in processes.values():
        pm.add_process(pcb)

    clock = 1
    while len(pm.terminated) < len(processes):
        pm.run(clock)
        clock += 1
    
    print(f"Mapa do disco: {sm.blocks}")


if __name__ == "__main__":
    main()
