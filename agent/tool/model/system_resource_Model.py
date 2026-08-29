from psutil._ntuples import scputimes
from pydantic import BaseModel, Field


class SystemResourceModel(BaseModel):
    # cpu
    cpu_physical_count: int | None = Field(description="物理核心数")
    logical_core_count: int | None = Field(description="逻辑核心数")
    cpu_percent: str = Field(description="CPU使用率")
    cpu_freq: str = Field(description="CPU频率")
    cpu_times: scputimes = Field(description="CPU时间")

    # 内存
    mem_total: str = Field(description="总内存")
    mem_used: str = Field(description="已用内存")
    mem_percent: str = Field(description="内存使用率")
    mem_swap_total: str = Field(description="交换内存总量")
