#!/usr/bin/env python3
"""
HFT-PacketFilter C Extensions Module

Ultra-high performance C extensions for HFT applications.
Provides microsecond-level latency optimizations.

Author: Tanzil github://@tanzil7890
License: Apache License 2.0
"""

try:
    # Import compiled Cython extensions
    from .fast_parser import FastPacketParser
    from .latency_tracker import UltraLowLatencyTracker
    from .memory_pool import HighPerformanceMemoryPool
    from .lock_free_queue import LockFreeQueue
    
    # Performance utilities
    from .performance_utils import (
        get_cpu_affinity,
        set_cpu_affinity,
        enable_numa_optimization,
        get_cache_line_size,
        prefetch_memory,
    )
    
    EXTENSIONS_AVAILABLE = True
    
except ImportError as e:
    # Fallback to pure Python implementations
    import warnings
    warnings.warn(
        f"C extensions not available ({e}). Using pure Python fallbacks. "
        "Performance will be significantly reduced. "
        "Run 'python setup.py build_ext --inplace' to build extensions.",
        UserWarning
    )
    
    from .fallbacks import (
        FastPacketParser,
        UltraLowLatencyTracker,
        HighPerformanceMemoryPool,
        LockFreeQueue,
    )
    
    # Stub performance utilities
    def get_cpu_affinity():
        return []
    
    def set_cpu_affinity(cores):
        return False
    
    def enable_numa_optimization():
        return False
    
    def get_cache_line_size():
        return 64
    
    def prefetch_memory(addr):
        pass
    
    EXTENSIONS_AVAILABLE = False

__all__ = [
    'FastPacketParser',
    'UltraLowLatencyTracker', 
    'HighPerformanceMemoryPool',
    'LockFreeQueue',
    'get_cpu_affinity',
    'set_cpu_affinity',
    'enable_numa_optimization',
    'get_cache_line_size',
    'prefetch_memory',
    'EXTENSIONS_AVAILABLE',
] 