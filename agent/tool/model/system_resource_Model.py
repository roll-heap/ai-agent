from pydantic import BaseModel, Field


class SystemResourceModel(BaseModel):
    # CPU
    cpu_physical_count: int | None = Field(description="CPU物理核心数")
    logical_core_count: int | None = Field(description="CPU逻辑核心数")
    cpu_percent: float = Field(description="CPU使用率百分比")
    cpu_freq_mhz: float | None = Field(description="当前CPU频率，单位MHz")

    # Memory
    mem_total_gb: float = Field(description="总内存，单位GB")
    mem_used_gb: float = Field(description="已使用内存，单位GB")
    mem_percent: float = Field(description="内存使用率百分比")
    mem_swap_total_gb: float = Field(description="交换内存总量，单位GB")
