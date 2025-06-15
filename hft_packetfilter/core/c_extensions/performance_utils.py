#!/usr/bin/env python3
"""
Performance Utilities

System-level performance optimization utilities for HFT applications.
Provides CPU affinity, NUMA optimization, and memory management.

Author: HFT-PacketFilter Development Team
License: Apache License 2.0
"""

import os
import sys
import psutil
import platform
import warnings
from typing import List, Optional, Dict, Any
import subprocess

def get_cpu_affinity() -> List[int]:
    """
    Get current CPU affinity.
    
    Returns:
        List[int]: List of CPU cores the process is bound to
    """
    try:
        process = psutil.Process()
        return list(process.cpu_affinity())
    except Exception as e:
        warnings.warn(f"Could not get CPU affinity: {e}")
        return []

def set_cpu_affinity(cores: List[int]) -> bool:
    """
    Set CPU affinity for current process.
    
    Args:
        cores: List of CPU core IDs to bind to
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        process = psutil.Process()
        process.cpu_affinity(cores)
        return True
    except Exception as e:
        warnings.warn(f"Could not set CPU affinity to {cores}: {e}")
        return False

def get_numa_nodes() -> Dict[int, List[int]]:
    """
    Get NUMA topology information.
    
    Returns:
        Dict[int, List[int]]: Mapping of NUMA node ID to CPU cores
    """
    numa_info = {}
    
    try:
        if platform.system() == "Linux":
            # Try to read from /sys/devices/system/node/
            for node_dir in os.listdir('/sys/devices/system/node/'):
                if node_dir.startswith('node'):
                    node_id = int(node_dir[4:])
                    cpulist_file = f'/sys/devices/system/node/{node_dir}/cpulist'
                    
                    if os.path.exists(cpulist_file):
                        with open(cpulist_file, 'r') as f:
                            cpulist = f.read().strip()
                            cores = parse_cpu_list(cpulist)
                            numa_info[node_id] = cores
                            
        elif platform.system() == "Darwin":
            # macOS doesn't have traditional NUMA, but we can provide CPU grouping
            cpu_count = psutil.cpu_count(logical=False)
            numa_info[0] = list(range(cpu_count))
            
    except Exception as e:
        warnings.warn(f"Could not determine NUMA topology: {e}")
        # Fallback: single NUMA node with all CPUs
        cpu_count = psutil.cpu_count(logical=True)
        numa_info[0] = list(range(cpu_count))
        
    return numa_info

def parse_cpu_list(cpulist: str) -> List[int]:
    """
    Parse Linux-style CPU list (e.g., "0-3,8-11").
    
    Args:
        cpulist: CPU list string
        
    Returns:
        List[int]: List of CPU core IDs
    """
    cores = []
    for part in cpulist.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            cores.extend(range(start, end + 1))
        else:
            cores.append(int(part))
    return cores

def enable_numa_optimization(numa_node: Optional[int] = None) -> bool:
    """
    Enable NUMA optimizations.
    
    Args:
        numa_node: Specific NUMA node to bind to, or None for auto-select
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        numa_topology = get_numa_nodes()
        
        if not numa_topology:
            warnings.warn("No NUMA nodes found")
            return False
            
        if numa_node is None:
            # Auto-select least loaded NUMA node
            numa_node = min(numa_topology.keys())
            
        if numa_node not in numa_topology:
            warnings.warn(f"NUMA node {numa_node} not found")
            return False
            
        # Set CPU affinity to the NUMA node
        cores = numa_topology[numa_node]
        success = set_cpu_affinity(cores)
        
        if success and platform.system() == "Linux":
            # Try to set memory policy using numactl
            try:
                pid = os.getpid()
                subprocess.run([
                    'numactl', '--membind', str(numa_node), 
                    '--cpunodebind', str(numa_node),
                    '--pid', str(pid)
                ], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                warnings.warn("Could not set NUMA memory policy (numactl not available)")
                
        return success
        
    except Exception as e:
        warnings.warn(f"NUMA optimization failed: {e}")
        return False

def get_cache_line_size() -> int:
    """
    Get CPU cache line size.
    
    Returns:
        int: Cache line size in bytes (defaults to 64 if unknown)
    """
    try:
        if platform.system() == "Linux":
            # Try to read from /sys/devices/system/cpu/cpu0/cache/
            for level in ['index0', 'index1', 'index2', 'index3']:
                cache_dir = f'/sys/devices/system/cpu/cpu0/cache/{level}'
                if os.path.exists(cache_dir):
                    coherency_file = os.path.join(cache_dir, 'coherency_line_size')
                    if os.path.exists(coherency_file):
                        with open(coherency_file, 'r') as f:
                            return int(f.read().strip())
                            
        elif platform.system() == "Darwin":
            # Try sysctl on macOS
            try:
                result = subprocess.run(['sysctl', 'hw.cachelinesize'], 
                                      capture_output=True, text=True, check=True)
                return int(result.stdout.split(':')[1].strip())
            except:
                pass
                
    except Exception:
        pass
        
    # Default cache line size for most modern CPUs
    return 64

def prefetch_memory(addr: int, size: int = 64) -> None:
    """
    Software prefetch memory (no-op in Python).
    
    Args:
        addr: Memory address to prefetch
        size: Size to prefetch (default: one cache line)
    """
    # This is a no-op in Python, but provides API compatibility
    # with C extensions that can do actual prefetching
    pass

def set_thread_priority(priority: str = "high") -> bool:
    """
    Set thread priority for better real-time performance.
    
    Args:
        priority: Priority level ("low", "normal", "high", "realtime")
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        process = psutil.Process()
        
        if priority == "realtime":
            # Highest priority (requires root on Linux)
            if platform.system() == "Linux":
                os.sched_setscheduler(0, os.SCHED_FIFO, os.sched_param(99))
            else:
                process.nice(psutil.HIGH_PRIORITY_CLASS)
        elif priority == "high":
            if platform.system() == "Windows":
                process.nice(psutil.HIGH_PRIORITY_CLASS)
            else:
                process.nice(-10)  # High priority
        elif priority == "normal":
            process.nice(psutil.NORMAL_PRIORITY_CLASS if platform.system() == "Windows" else 0)
        elif priority == "low":
            if platform.system() == "Windows":
                process.nice(psutil.IDLE_PRIORITY_CLASS)
            else:
                process.nice(10)  # Low priority
                
        return True
        
    except Exception as e:
        warnings.warn(f"Could not set thread priority to {priority}: {e}")
        return False

def optimize_memory_allocation() -> bool:
    """
    Optimize memory allocation for better performance.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if platform.system() == "Linux":
            # Try to set memory allocation policy
            try:
                # Disable swap for this process
                with open(f'/proc/{os.getpid()}/oom_score_adj', 'w') as f:
                    f.write('-1000')  # Protect from OOM killer
            except:
                pass
                
            # Try to lock memory pages
            try:
                import mlock
                mlock.mlockall()
            except ImportError:
                warnings.warn("mlock not available, memory pages not locked")
                
        return True
        
    except Exception as e:
        warnings.warn(f"Memory optimization failed: {e}")
        return False

def get_performance_info() -> Dict[str, Any]:
    """
    Get comprehensive performance information.
    
    Returns:
        Dict[str, Any]: Performance information
    """
    info = {
        'platform': platform.system(),
        'architecture': platform.machine(),
        'cpu_count_physical': psutil.cpu_count(logical=False),
        'cpu_count_logical': psutil.cpu_count(logical=True),
        'cpu_freq_max': None,
        'memory_total_gb': psutil.virtual_memory().total / (1024**3),
        'memory_available_gb': psutil.virtual_memory().available / (1024**3),
        'cache_line_size': get_cache_line_size(),
        'cpu_affinity': get_cpu_affinity(),
        'numa_nodes': get_numa_nodes(),
    }
    
    try:
        cpu_freq = psutil.cpu_freq()
        if cpu_freq:
            info['cpu_freq_max'] = cpu_freq.max
    except:
        pass
        
    return info

def setup_hft_optimizations(
    cpu_cores: Optional[List[int]] = None,
    numa_node: Optional[int] = None,
    thread_priority: str = "high",
    lock_memory: bool = True
) -> Dict[str, bool]:
    """
    Setup comprehensive HFT optimizations.
    
    Args:
        cpu_cores: Specific CPU cores to bind to
        numa_node: NUMA node to optimize for
        thread_priority: Thread priority level
        lock_memory: Whether to lock memory pages
        
    Returns:
        Dict[str, bool]: Results of each optimization attempt
    """
    results = {}
    
    # Set CPU affinity
    if cpu_cores:
        results['cpu_affinity'] = set_cpu_affinity(cpu_cores)
    else:
        results['cpu_affinity'] = True
        
    # Enable NUMA optimization
    results['numa_optimization'] = enable_numa_optimization(numa_node)
    
    # Set thread priority
    results['thread_priority'] = set_thread_priority(thread_priority)
    
    # Optimize memory allocation
    if lock_memory:
        results['memory_optimization'] = optimize_memory_allocation()
    else:
        results['memory_optimization'] = True
        
    return results

def validate_hft_environment() -> Dict[str, Any]:
    """
    Validate that the environment is suitable for HFT.
    
    Returns:
        Dict[str, Any]: Validation results and recommendations
    """
    results = {
        'suitable_for_hft': True,
        'warnings': [],
        'recommendations': [],
        'system_info': get_performance_info()
    }
    
    # Check CPU count
    cpu_count = psutil.cpu_count(logical=False)
    if cpu_count < 4:
        results['warnings'].append(f"Only {cpu_count} physical CPU cores available")
        results['recommendations'].append("Consider upgrading to a system with more CPU cores")
        
    # Check memory
    memory_gb = psutil.virtual_memory().total / (1024**3)
    if memory_gb < 16:
        results['warnings'].append(f"Only {memory_gb:.1f}GB memory available")
        results['recommendations'].append("Consider upgrading to at least 16GB RAM")
        
    # Check if running as root (for real-time priorities)
    if platform.system() == "Linux" and os.getuid() != 0:
        results['warnings'].append("Not running as root - real-time priorities unavailable")
        results['recommendations'].append("Consider running with elevated privileges for real-time scheduling")
        
    # Check for HFT-optimized kernel
    if platform.system() == "Linux":
        try:
            with open('/proc/version', 'r') as f:
                kernel_version = f.read()
                if 'rt' not in kernel_version.lower():
                    results['warnings'].append("Not using real-time kernel")
                    results['recommendations'].append("Consider using RT_PREEMPT kernel for better latency")
        except:
            pass
            
    # Determine overall suitability
    if len(results['warnings']) > 2:
        results['suitable_for_hft'] = False
        
    return results 