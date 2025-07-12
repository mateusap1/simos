import pytest

from simos.managers.process import ProcessManager, PCB, State


def test_add_process(process_manager: ProcessManager):
    process = PCB(
        pid=0,
        priority=0,
        init_duration=2,
        cpu_duration=3,
        memory_offset=0,
        memory_alloc=64,
    )
    process_manager.add_process(process, 42)

    process_added = process_manager.process_table[process.pid]
    assert process_added.arrive_new_time == 42
    assert process_added.state == State.NEW

    assert len(process_manager.new_queue) == 1
    assert process.pid == process_manager.new_queue.index(0)


def test_add_process(process_manager: ProcessManager):
    process = PCB(
        pid=0,
        priority=0,
        init_duration=2,
        cpu_duration=3,
        memory_offset=0,
        memory_alloc=64,
    )
    process_manager.add_process(process, 42)

    process_added = process_manager.process_table[process.pid]
    assert process_added.arrive_new_time == 42
    assert process_added.state == State.NEW

    assert len(process_manager.new_queue) == 1
    assert process.pid == process_manager.new_queue.index(0)

