import pytest

from simos.managers.process import ProcessManager

@pytest.fixture(scope="module")
def process_manager():
    return ProcessManager()