class SimulationError(Exception):
    pass


class SystemError(Exception):
    pass


class SystemEvent:
    pass


class ScheduleEvent(SystemEvent):
    pass


class Instruction:
    def execute(self) -> None:
        raise NotImplementedError()
