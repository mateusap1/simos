import argparse


from simos.managers.process import (
    PCB,
    CreateFileInstruction,
    DeleteFileInstruction,
    ProcessManager,
)
from simos.resources import Resource


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("process_file", help="Arquivo de processos")
    parser.add_argument("ops_file", help="Arquivo de operações")
    args = parser.parse_args()

    # Lê processos
    processes: dict[int, PCB] = {}
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
            if prn == "1":
                pcb.use_resources.append(Resource.PRINTER)
            if scn == "1":
                pcb.use_resources.append(Resource.SCANNER)
            if modem == "1":
                pcb.use_resources.append(Resource.MODEM)
            if disk == "1":
                pcb.use_resources.append(Resource.DISK)
            processes[pid] = pcb

    # Lê operações de arquivos
    with open(args.ops_file) as f:
        total_blocks = int(f.readline().strip())
        n_segments = int(f.readline().strip())
        for _ in range(n_segments):
            f.readline()
        for line in f:
            line = line.strip()
            if not line:
                continue
            pid_str, op_code, filename, *rest = [p.strip() for p in line.split(",")]
            pid = int(pid_str)
            if op_code == "0":
                blocks_n = int(rest[0])
                instr = CreateFileInstruction(pid, filename, blocks_n)
            else:
                instr = DeleteFileInstruction(pid, filename)
            if pid in processes:
                processes[pid].instructions.append(instr)
            else:
                print(f"Processo {pid} não existe")

    pm = ProcessManager()
    for pcb in processes.values():
        pm.add_process(pcb)

    clock = 0
    while len(pm.terminated) < len(processes):
        pm.run(clock)
        clock += 1


if __name__ == "__main__":
    main()