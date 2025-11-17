import pytest
from unittest.mock import MagicMock
import time

from src.resources.system_monitor import SystemResourceMonitor
from src.resources.base_monitor import BaseResourceMonitor

# --- MOCK CONSTANTS ---
MOCK_TIMESTAMP = time.time()
MOCK_AVAILABLE_BYTES = 4 * 1024**3 # 4 GB
MOCK_TOTAL_BYTES = 8 * 1024**3 # 8 GB
MEGABYTE = 1024 * 1024
MOCK_CPU_PERCENT = 20.0
MOCK_TOTAL_CORES = 8
MOCK_DISK_USAGE = MagicMock(percent=35.0)

MOCK_NETWORK_IO_DICT = {'bytes_sent': 1000, 'bytes_recv': 200}
MOCK_NET_IO_COUNTERS_OBJ = MagicMock()
MOCK_NET_IO_COUNTERS_OBJ._asdict.return_value = MOCK_NETWORK_IO_DICT

MOCK_VIRTUAL_MEMORY = MagicMock(
    total=MOCK_TOTAL_BYTES,
    available=MOCK_AVAILABLE_BYTES,
    percent=50.0
)

MOCK_PROCESSES = [
    {'pid': 101, 'name': 'agent_task_1', 'cpu_percent': 15.0, 'memory_percent': 3.0, 'status': 'running', 'username': 'user'},
    {'pid': 102, 'name': 'main_loop', 'cpu_percent': 5.0, 'memory_percent': 1.0, 'status': 'sleeping', 'username': 'user'},
    {'pid': 103, 'name': 'system_proc', 'cpu_percent': 1.0, 'memory_percent': 0.5, 'status': 'running', 'username': 'system'},
]

@pytest.fixture
def monitor():
    """Fixture to create a SystemResourceMonitor instance for tests."""
    return SystemResourceMonitor(top_n_processes=2)

def setup_mocker_for_snapshot(mocker):
    """Sets up all necessary mocks for the comprehensive snapshot/load details method."""
    # Use mocker.patch for clean patching
    mocker.patch('psutil.cpu_count', return_value=MOCK_TOTAL_CORES)
    mocker.patch('psutil.cpu_percent', return_value=MOCK_CPU_PERCENT)
    mocker.patch('psutil.virtual_memory', return_value=MOCK_VIRTUAL_MEMORY)
    mocker.patch('psutil.disk_usage', return_value=MOCK_DISK_USAGE)
    mocker.patch('psutil.net_io_counters', return_value=MOCK_NET_IO_COUNTERS_OBJ)
    mocker.patch('time.time', return_value=MOCK_TIMESTAMP)

    # Mock process iterator
    mock_proc_iterable = [MagicMock(info=p) for p in MOCK_PROCESSES]
    mocker.patch('psutil.process_iter', return_value=mock_proc_iterable)

def test_monitor_implements_base_interface(monitor):
    """Checks if the concrete class correctly inherits from the ABC."""
    assert isinstance(monitor, BaseResourceMonitor)

def test_get_available_ram_mb(monitor, mocker):
    """Tests that available RAM is correctly converted from bytes to MB."""
    mocker.patch('psutil.virtual_memory', return_value=MOCK_VIRTUAL_MEMORY)

    expected_mb = int(MOCK_AVAILABLE_BYTES / MEGABYTE)
    result = monitor.get_available_ram_mb()
    assert result == expected_mb

def test_get_available_cpu_cores(monitor, mocker):
    """Tests that available cores are calculated correctly."""
    mocker.patch('psutil.cpu_count', return_value=MOCK_TOTAL_CORES)
    mocker.patch('psutil.cpu_percent', return_value=MOCK_CPU_PERCENT)

    expected_cores = MOCK_TOTAL_CORES * (1.0 - (MOCK_CPU_PERCENT / 100.0))
    result = monitor.get_available_cpu_cores()
    assert result == expected_cores

def test_get_system_lead_details_structure_and_sorting(monitor, mocker):
    """Test comprehensive system snapshot details and top N sorting."""
    setup_mocker_for_snapshot(mocker)
    result = monitor.get_system_load_details()

    # Check top processes was limited to 2 and sorted by CPU
    top_processes = result['top_processes']
    assert len(top_processes) == 2

    assert top_processes[0]['pid'] == 101
    assert top_processes[0]['cpu_percent'] == pytest.approx(15.0)

def test_get_system_load_details_error_handling(monitor, mocker):
    """Tests that the monitor returns a safe, zeroed state on a critical failure."""

    mocker.patch('psutil.cpu_percent', side_effect=Exception("Critical system error"))

    result = monitor.get_system_load_details()

    assert result['cpu_utilization_percent'] == 100.0
    assert 'error' in result['extra_data']
    assert result['memory_total_mb'] == 0