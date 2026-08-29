import psutil

from agent.tool.model.system_resource_Model import SystemResourceModel


class SystemResourceDao:
    @staticmethod
    def system_resource() -> SystemResourceModel:
        # cpu
        cpu_physical_count = psutil.cpu_count(logical=False)
        logical_core_count = psutil.cpu_count(logical=True)
        cpu_percent = f"{psutil.cpu_percent(interval=1)}%"
        cpu_freq = f"{psutil.cpu_freq().current:.0f} MHz"
        cpu_times = psutil.cpu_times()

        # 内存
        mem = psutil.virtual_memory()
        mem_total = f"{mem.total / (1024 ** 3):.2f} GB"
        mem_used = f"{mem.used / (1024 ** 3):.2f} GB"
        mem_percent = f"{mem.percent}%"
        swap = psutil.swap_memory()
        mem_swap_total = f"{swap.total / (1024 ** 3):.2f} GB"

        return SystemResourceModel(
            cpu_physical_count = cpu_physical_count,
            logical_core_count = logical_core_count,
            cpu_percent = cpu_percent,
            cpu_freq = cpu_freq,
            cpu_times = cpu_times,
            mem_total = mem_total,
            mem_used = mem_used,
            mem_percent = mem_percent,
            mem_swap_total = mem_swap_total
        )
