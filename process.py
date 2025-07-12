from simos.managers.process import ProcessManager



def main():
    clock = 0
    process_manager = ProcessManager()
    while True:
        process_manager.run(clock)
        clock += 1