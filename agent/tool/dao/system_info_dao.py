import os
import platform

from agent.tool.model.system_info_model import SystemInfoModel


class SystemInfoDao:
    @staticmethod
    def get_system_info() -> SystemInfoModel:
        """
        获取操作系统信息
        :return:
        """
        os_name = platform.system()
        os_version = platform.version()
        architecture = platform.machine()
        hostname = platform.node()
        python_version = platform.python_version()
        current_work_directory = os.getcwd()
        return SystemInfoModel(
                os_name = os_name,
                os_version = os_version,
                architecture = architecture,
                hostname = hostname,
                python_version = python_version,
                current_work_directory = current_work_directory
            )

# print("=== platform 模块信息 ===")
# print(f"操作系统名称: {platform.system()}")          # 如 'Windows', 'Linux'[reference:25]
# print(f"操作系统版本: {platform.version()}")         # 系统版本号[reference:26]
# print(f"系统详细信息: {platform.platform()}")        # 人类可读的系统信息[reference:27]
# print(f"机器架构: {platform.machine()}")             # 如 'AMD64'[reference:28]
# print(f"处理器名称: {platform.processor()}")         # 处理器信息[reference:29]
# print(f"网络主机名: {platform.node()}")              # 网络名称[reference:30]
# print(f"Python版本: {platform.python_version()}")    # Python版本号[reference:31]
# print(os.getcwd())