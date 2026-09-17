"""设备画像测试。"""

import pytest

from app.data.device_profile import DeviceProfile, DeviceProfileReader


class TestDeviceProfile:
    def test_recommended_cache_size_low_end(self):
        """低配设备应返回较小的缓存大小。"""
        profile = DeviceProfile(is_low_end_device=True, memory_total_gb=1.5, cpu_count=1)
        assert profile.get_recommended_cache_size() == 100

    def test_recommended_cache_size_small_memory(self):
        """内存 < 4GB 返回 200。"""
        profile = DeviceProfile(is_low_end_device=False, memory_total_gb=3.0, cpu_count=2)
        assert profile.get_recommended_cache_size() == 200

    def test_recommended_cache_size_medium_memory(self):
        """内存 4-8GB 返回 500。"""
        profile = DeviceProfile(is_low_end_device=False, memory_total_gb=6.0, cpu_count=4)
        assert profile.get_recommended_cache_size() == 500

    def test_recommended_cache_size_large_memory(self):
        """内存 >= 8GB 返回 1000。"""
        profile = DeviceProfile(is_low_end_device=False, memory_total_gb=16.0, cpu_count=8)
        assert profile.get_recommended_cache_size() == 1000

    def test_rate_limit_bypass_low_memory(self):
        """内存 < 2GB 应使用 rate limit bypass。"""
        profile = DeviceProfile(memory_total_gb=1.5, cpu_count=4)
        assert profile.should_use_rate_limit_bypass() is True

    def test_rate_limit_bypass_low_cpu(self):
        """CPU <= 1 核应使用 rate limit bypass。"""
        profile = DeviceProfile(memory_total_gb=8.0, cpu_count=1)
        assert profile.should_use_rate_limit_bypass() is True

    def test_rate_limit_bypass_normal(self):
        """正常配置不使用 bypass。"""
        profile = DeviceProfile(memory_total_gb=8.0, cpu_count=4)
        assert profile.should_use_rate_limit_bypass() is False

    def test_estimate_concurrency_single_cpu(self):
        """单核返回 1。"""
        profile = DeviceProfile(cpu_count=1)
        assert profile.estimate_api_concurrency() == 1

    def test_estimate_concurrency_quad_core(self):
        """4 核返回 2。"""
        profile = DeviceProfile(cpu_count=4)
        assert profile.estimate_api_concurrency() == 2

    def test_estimate_concurrency_high_cpu(self):
        """8+ 核返回 min(4, cpu/2)。"""
        profile = DeviceProfile(cpu_count=16)
        assert profile.estimate_api_concurrency() == 4


class TestDeviceProfileReader:
    def test_read_returns_valid_profile(self):
        """read() 返回有效的 DeviceProfile。"""
        profile = DeviceProfileReader.read()
        assert isinstance(profile, DeviceProfile)
        assert profile.cpu_count > 0
        assert profile.memory_total_gb > 0

    def test_get_cached_returns_same_instance(self):
        """get_cached() 返回同一实例。"""
        p1 = DeviceProfileReader.get_cached()
        p2 = DeviceProfileReader.get_cached()
        assert p1 is p2
