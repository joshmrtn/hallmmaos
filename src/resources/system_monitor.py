import psutil
import time
from typing import List
import logging

from src.resources.base_monitor import BaseResourceMonitor
from src.resources.resource_types import SystemHealth, ProcessHealth

logger = logging.getLogger(__name__)

class SystemResourceMonitor(BaseResourceMonitor):
    """
    Monitors and captures system resource health snapshots.
    """

    # Define MB
    MEGABYTE = 1024 * 1024

    def __init__(self, top_n_processes: int = 5):
        """
        Initializes the monitor.

        Args:
            top_n_processes (int): The number of top resource-consuming processes to track.
        """
        self.top_n_processes = top_n_processes
        psutil.cpu_percent(interval=None)

    def _get_system_snapshot(self) -> SystemHealth:
        """
        Internal method to gather a complete SystemHealth snapshot for 
        use by the three public interface methods.
        """
        try:
            # Gather system metrics.
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')

            mem_total_mb = int(memory_info.total / self.MEGABYTE)
            mem_available_mb = int(memory_info.available / self.MEGABYTE)

            net_io = psutil.net_io_counters()._asdict()

            # Gather process metrics.
            process_data: List[ProcessHealth] = []
            process_list = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'username']):
                try:
                    process_list.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            top_processes_info = sorted(
                process_list,
                key=lambda x: x.get('cpu_percent', 0.0),
                reverse=True
            )[:self.top_n_processes]

            for p_info in top_processes_info:
                process_data.append(ProcessHealth(
                    pid=p_info.get('pid', 0),
                    name=p_info.get('name', 'unknown'),
                    cpu_percent=p_info.get('cpu_percent', 0.0),
                    memory_percent=p_info.get('memory_percent', 0.0),
                    status=p_info.get('status', 'unknown'),
                    username=p_info.get('username', 'system')
                ))

            # Compile and return a SystemHealth object
            return SystemHealth(
                timestamp=time.time(),
                cpu_utilization_percent=cpu_usage,
                memory_total_mb=mem_total_mb,
                memory_available_mb=mem_available_mb,
                memory_usage_percent=memory_info.percent,
                disk_usage_percent=disk_info.percent,
                network_io=net_io,
                process_count=len(process_list),
                top_processes=process_data,
                extra_data={"cpu_cores": psutil.cpu_count(logical=True)}
            )
        
        except Exception as e:
            logger.warning(f"Error during system snapshot: {e}.", exc_info=True)
            # Return a zeroed, safe state on failure.
            return SystemHealth(
                timestamp=time.time(),
                cpu_utilization_percent=100.0,
                memory_total_mb=0,
                memory_available_mb=0,
                memory_usage_percent=100.0,
                disk_usage_percent=0.0,
                network_io={},
                process_count=0,
                top_processes=[],
                extra_data={"error": str(e)}
            )
        
    def get_available_ram_mb(self) -> int:
        """
        Implements the contract: Retrieves the amount of RAM available in MB.
        """
        return int(psutil.virtual_memory().available / self.MEGABYTE)
    
    def get_available_cpu_cores(self) -> float:
        """
        Implements the contract: Retrieves the available CPU capacity.

        Calculated as Total Logical Cores * (1 - CPU Utilization %)
        """

        total_cores = psutil.cpu_count(logical=True)
        current_utilization_percent = psutil.cpu_percent(interval=0.1)

        available_cores = total_cores * (1.0 - (current_utilization_percent / 100))

        return available_cores
    
    def get_system_load_details(self):
        """
        Implements the contract: Retrieves a detailed dictionary of system-wide load.
        """
        return self._get_system_snapshot().model_dump()