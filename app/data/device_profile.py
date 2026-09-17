"""设备画像 - 读取本机硬件信息用于服务端决策。"""

import platform
import psutil
import os
from typing import Optional

from pydantic import BaseModel


class DeviceProfile(BaseModel):
    """本机硬件信息画像（服务端自用，不暴露给客户端）。"""
    
    hostname: str = "unknown"
    os_name: str = "unknown"
    os_version: str = "unknown"
    python_version: str = "unknown"
    cpu_count: int = 0
    cpu_percent: float = 0.0
    memory_total_gb: float = 0.0
    memory_available_gb: float = 0.0
    memory_percent: float = 0.0
    disk_total_gb: float = 0.0
    disk_available_gb: float = 0.0
    is_low_end_device: bool = False

    def get_recommended_cache_size(self) -> int:
        """
        根据本机内存推荐缓存大小。
        
        Returns:
            缓存条目数量上限
        """
        if self.is_low_end_device:
            return 100
        elif self.memory_total_gb < 4:
            return 200
        elif self.memory_total_gb < 8:
            return 500
        else:
            return 1000

    def should_use_rate_limit_bypass(self) -> bool:
        """
        决定是否使用 GitHub Token 绕过速率限制。
        
        Returns:
            True 表示应该使用认证 Token
        """
        return self.memory_total_gb < 2 or self.cpu_count < 2

    def estimate_api_concurrency(self) -> int:
        """
        根据 CPU 核心数估算合适的并发数。
        
        Returns:
            推荐并发数
        """
        cpu = self.cpu_count
        if cpu <= 1:
            return 1
        elif cpu <= 4:
            return min(2, cpu)
        else:
            return min(4, cpu // 2)


class DeviceProfileReader:
    """读取本机硬件信息的工具类。"""

    @staticmethod
    def read() -> DeviceProfile:
        """
        读取当前机器的硬件信息。
        
        Returns:
            DeviceProfile 实例
        """
        # OS 信息
        os_name = platform.system()
        os_version = platform.release()
        hostname = platform.node()

        # CPU 信息
        cpu_count = psutil.cpu_count(logical=True) or 1
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # 内存信息
        mem = psutil.virtual_memory()
        memory_total_gb = mem.total / (1024 ** 3)
        memory_available_gb = mem.available / (1024 ** 3)
        memory_percent = mem.percent

        # 磁盘信息（根分区）
        disk = psutil.disk_usage("/")
        disk_total_gb = disk.total / (1024 ** 3)
        disk_available_gb = disk.free / (1024 ** 3)

        # 判断是否为低配设备（内存 < 2GB 或 CPU <= 1 核）
        is_low_end = memory_total_gb < 2 or cpu_count <= 1

        return DeviceProfile(
            hostname=hostname,
            os_name=os_name,
            os_version=os_version,
            python_version=platform.python_version(),
            cpu_count=cpu_count,
            cpu_percent=cpu_percent,
            memory_total_gb=round(memory_total_gb, 2),
            memory_available_gb=round(memory_available_gb, 2),
            memory_percent=round(memory_percent, 1),
            disk_total_gb=round(disk_total_gb, 2),
            disk_available_gb=round(disk_available_gb, 2),
            is_low_end_device=is_low_end,
        )

    @staticmethod
    def get_cached() -> DeviceProfile:
        """
        获取缓存的设备画像（避免重复读取）。
        
        Returns:
            DeviceProfile 实例
        """
        if not hasattr(DeviceProfileReader, "_cached"):
            DeviceProfileReader._cached = DeviceProfileReader.read()
        return DeviceProfileReader._cached


# 全局设备画像实例
device_profile = DeviceProfileReader.get_cached()
