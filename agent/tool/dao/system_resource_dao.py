import psutil

from agent.tool.domain import SystemResourceModel


class SystemResourceDao:
    @staticmethod
    def system_resource() -> SystemResourceModel:
        cpu_freq = psutil.cpu_freq()
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return SystemResourceModel(
            # CPU
            cpu_physical_count=psutil.cpu_count(logical=False),
            logical_core_count=psutil.cpu_count(logical=True),
            cpu_percent=psutil.cpu_percent(interval=1),
            cpu_freq_mhz=(cpu_freq.current if cpu_freq else None),
            # Memory
            mem_total_gb=mem.total / (1024 ** 3),
            mem_used_gb=mem.used / (1024 ** 3),
            mem_percent=mem.percent,
            mem_swap_total_gb=swap.total / (1024 ** 3)
        )