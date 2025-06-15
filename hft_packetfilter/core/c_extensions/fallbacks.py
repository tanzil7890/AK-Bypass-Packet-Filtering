#!/usr/bin/env python3
"""
Fallback Python Implementations

Pure Python implementations used when C extensions are not available.
Provides same API but with reduced performance.

Author: HFT-PacketFilter Development Team
License: Apache License 2.0
"""

import time
import struct
import threading
import queue
import statistics
from collections import deque
from typing import Optional, Dict, Any, List
import warnings

class FastPacketParser:
    """Pure Python packet parser fallback."""
    
    def __init__(self):
        self.packets_parsed = 0
        self.bytes_processed = 0
        self.parse_time_ns = 0
        
        # Exchange port mappings
        self.exchange_ports = {
            # NYSE
            4001: ('NYSE', 1), 9001: ('NYSE', 1), 8001: ('NYSE', 1), 7001: ('NYSE', 1),
            # NASDAQ
            4002: ('NASDAQ', 2), 9002: ('NASDAQ', 2), 8002: ('NASDAQ', 2), 7002: ('NASDAQ', 2),
            # CBOE
            4003: ('CBOE', 3), 9003: ('CBOE', 3), 8003: ('CBOE', 3), 7003: ('CBOE', 3),
        }
        
    def _is_fix_protocol(self, payload: bytes) -> bool:
        """Check if payload contains FIX protocol."""
        if len(payload) < 5:
            return False
        return payload[:5] == b'8=FIX'
        
    def parse_packet_fast(self, packet_data: bytes) -> Optional[Dict[str, Any]]:
        """
        Parse packet data (pure Python implementation).
        
        Args:
            packet_data: Raw packet bytes
            
        Returns:
            dict: Parsed packet information or None
        """
        start_time = time.time_ns()
        
        try:
            if len(packet_data) < 14:  # Minimum Ethernet frame
                return None
                
            # Simple Ethernet header parsing
            eth_type = struct.unpack('>H', packet_data[12:14])[0]
            if eth_type != 0x0800:  # Not IPv4
                return None
                
            if len(packet_data) < 34:  # Minimum IPv4 frame
                return None
                
            # Parse IPv4 header
            ip_header = packet_data[14:34]
            version_ihl = ip_header[0]
            if (version_ihl >> 4) != 4:  # Not IPv4
                return None
                
            protocol = ip_header[9]
            src_ip = struct.unpack('>I', ip_header[12:16])[0]
            dest_ip = struct.unpack('>I', ip_header[16:20])[0]
            
            ip_header_len = (version_ihl & 0x0F) * 4
            
            if protocol == 6:  # TCP
                if len(packet_data) < 14 + ip_header_len + 20:
                    return None
                    
                tcp_header = packet_data[14 + ip_header_len:14 + ip_header_len + 20]
                src_port, dest_port = struct.unpack('>HH', tcp_header[0:4])
                
                # Check payload for FIX
                tcp_header_len = ((tcp_header[12] >> 4) & 0x0F) * 4
                payload_start = 14 + ip_header_len + tcp_header_len
                
                is_fix = False
                if payload_start < len(packet_data):
                    payload = packet_data[payload_start:]
                    is_fix = self._is_fix_protocol(payload)
                    
            elif protocol == 17:  # UDP
                if len(packet_data) < 14 + ip_header_len + 8:
                    return None
                    
                udp_header = packet_data[14 + ip_header_len:14 + ip_header_len + 8]
                src_port, dest_port = struct.unpack('>HH', udp_header[0:4])
                
                # Check payload for FIX
                payload_start = 14 + ip_header_len + 8
                is_fix = False
                if payload_start < len(packet_data):
                    payload = packet_data[payload_start:]
                    is_fix = self._is_fix_protocol(payload)
                    
            else:
                return None
                
            # Check if trading-related
            exchange_info = (
                self.exchange_ports.get(src_port) or 
                self.exchange_ports.get(dest_port)
            )
            
            if not exchange_info:
                return None
                
            exchange_name, exchange_id = exchange_info
            
            # Update statistics
            self.packets_parsed += 1
            self.bytes_processed += len(packet_data)
            self.parse_time_ns += time.time_ns() - start_time
            
            return {
                'src_port': src_port,
                'dest_port': dest_port,
                'protocol': 'TCP' if protocol == 6 else 'UDP',
                'exchange_id': exchange_id,
                'exchange_name': exchange_name,
                'is_fix': is_fix,
                'packet_size': len(packet_data),
                'src_ip': src_ip,
                'dest_ip': dest_ip,
            }
            
        except Exception:
            return None
            
    def get_statistics(self):
        """Get parsing statistics."""
        return {
            'packets_parsed': self.packets_parsed,
            'bytes_processed': self.bytes_processed,
            'parse_time_ns': self.parse_time_ns,
        }
        
    def reset_statistics(self):
        """Reset parsing statistics."""
        self.packets_parsed = 0
        self.bytes_processed = 0
        self.parse_time_ns = 0


class UltraLowLatencyTracker:
    """Pure Python latency tracker fallback."""
    
    def __init__(self, max_samples: int = 100000, target_latency_us: float = 500.0):
        self.max_samples = max_samples
        self.target_latency_us = target_latency_us
        self.samples = deque(maxlen=max_samples)
        self.total_samples = 0
        self.violation_count = 0
        self.lock = threading.RLock()
        
    def record_latency(self, latency_us: float, exchange_id: int = 0, protocol: str = 'TCP'):
        """Record a latency measurement."""
        with self.lock:
            timestamp_ns = time.time_ns()
            sample = {
                'timestamp_ns': timestamp_ns,
                'latency_us': latency_us,
                'exchange_id': exchange_id,
                'protocol': protocol,
            }
            
            self.samples.append(sample)
            self.total_samples += 1
            
            if latency_us > self.target_latency_us:
                self.violation_count += 1
                
    def record_packet_latency(self, send_time_ns: int, recv_time_ns: int, 
                             exchange_id: int = 0, protocol: str = 'TCP'):
        """Record latency from packet timestamps."""
        if recv_time_ns <= send_time_ns:
            return
            
        latency_us = (recv_time_ns - send_time_ns) / 1000.0
        self.record_latency(latency_us, exchange_id, protocol)
        
    def get_current_latency_us(self) -> float:
        """Get the most recent latency measurement."""
        with self.lock:
            if not self.samples:
                return 0.0
            return self.samples[-1]['latency_us']
            
    def get_percentile(self, percentile: float) -> float:
        """Calculate latency percentile."""
        with self.lock:
            if not self.samples:
                return 0.0
                
            latencies = [s['latency_us'] for s in self.samples]
            try:
                return statistics.quantiles(latencies, n=100)[int(percentile) - 1]
            except (IndexError, statistics.StatisticsError):
                return 0.0
                
    def get_statistics(self) -> Dict[str, float]:
        """Get comprehensive latency statistics."""
        with self.lock:
            if not self.samples:
                return {
                    'count': 0, 'min_us': 0.0, 'max_us': 0.0, 'mean_us': 0.0, 'std_us': 0.0,
                    'p50_us': 0.0, 'p95_us': 0.0, 'p99_us': 0.0, 'p99_9_us': 0.0,
                    'violation_rate': 0.0, 'target_us': self.target_latency_us,
                }
                
            latencies = [s['latency_us'] for s in self.samples]
            
            try:
                mean_us = statistics.mean(latencies)
                std_us = statistics.stdev(latencies) if len(latencies) > 1 else 0.0
            except statistics.StatisticsError:
                mean_us = std_us = 0.0
                
            return {
                'count': self.total_samples,
                'min_us': min(latencies),
                'max_us': max(latencies),
                'mean_us': mean_us,
                'std_us': std_us,
                'p50_us': self.get_percentile(50.0),
                'p95_us': self.get_percentile(95.0),
                'p99_us': self.get_percentile(99.0),
                'p99_9_us': self.get_percentile(99.9),
                'violation_rate': (self.violation_count / self.total_samples) * 100.0,
                'target_us': self.target_latency_us,
            }
            
    def reset_statistics(self):
        """Reset all statistics."""
        with self.lock:
            self.samples.clear()
            self.total_samples = 0
            self.violation_count = 0
            
    def set_target_latency(self, target_us: float):
        """Set target latency threshold."""
        self.target_latency_us = target_us
        
    def get_sample_count(self) -> int:
        """Get current number of samples."""
        return self.total_samples
        
    def is_violation(self, latency_us: float) -> bool:
        """Check if latency exceeds target."""
        return latency_us > self.target_latency_us


class HighPerformanceMemoryPool:
    """Pure Python memory pool fallback."""
    
    def __init__(self, pool_size: int = 1024*1024, block_size: int = 1024, use_mmap: bool = False):
        self.pool_size = pool_size
        self.block_size = block_size
        self.num_blocks = pool_size // block_size
        
        # Use simple list-based pool
        self.free_blocks = queue.Queue(maxsize=self.num_blocks)
        self.allocated_blocks = set()
        
        # Pre-allocate all blocks
        for _ in range(self.num_blocks):
            block = bytearray(block_size)
            self.free_blocks.put(block)
            
        self.total_allocations = 0
        self.total_deallocations = 0
        self.lock = threading.RLock()
        
    def allocate(self, size: int = 0) -> Optional[memoryview]:
        """Allocate a memory block."""
        try:
            with self.lock:
                block = self.free_blocks.get_nowait()
                self.allocated_blocks.add(id(block))
                self.total_allocations += 1
                return memoryview(block)
        except queue.Empty:
            return None
            
    def deallocate(self, memview):
        """Deallocate a memory block."""
        if memview is None:
            return
            
        with self.lock:
            block_id = id(memview.obj)
            if block_id in self.allocated_blocks:
                self.allocated_blocks.remove(block_id)
                # Clear the block
                memview.obj[:] = bytearray(len(memview.obj))
                self.free_blocks.put(memview.obj)
                self.total_deallocations += 1
                
    def allocate_packet_buffer(self):
        """Allocate packet buffer."""
        return self.allocate()
        
    def allocate_message_buffer(self):
        """Allocate message buffer."""
        return self.allocate()
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get memory pool statistics."""
        with self.lock:
            return {
                'pool_size_bytes': self.pool_size,
                'block_size_bytes': self.block_size,
                'total_blocks': self.num_blocks,
                'blocks_allocated': len(self.allocated_blocks),
                'blocks_free': self.free_blocks.qsize(),
                'utilization_percent': (len(self.allocated_blocks) / self.num_blocks) * 100.0,
                'total_allocations': self.total_allocations,
                'total_deallocations': self.total_deallocations,
                'use_mmap': False,
            }
            
    def reset_pool(self):
        """Reset the memory pool."""
        with self.lock:
            # Clear allocated blocks
            self.allocated_blocks.clear()
            
            # Recreate free blocks
            while not self.free_blocks.empty():
                try:
                    self.free_blocks.get_nowait()
                except queue.Empty:
                    break
                    
            for _ in range(self.num_blocks):
                block = bytearray(self.block_size)
                self.free_blocks.put(block)
                
    def prefault_memory(self):
        """Pre-fault memory (no-op in Python)."""
        pass
        
    def get_block_size(self) -> int:
        """Get block size."""
        return self.block_size
        
    def get_free_blocks(self) -> int:
        """Get number of free blocks."""
        return self.free_blocks.qsize()


class LockFreeQueue:
    """Pure Python queue fallback (uses locks)."""
    
    def __init__(self, capacity: int = 65536):
        self.capacity = capacity
        self.queue = queue.Queue(maxsize=capacity)
        self.total_enqueued = 0
        self.total_dequeued = 0
        self.total_failed_enqueues = 0
        self.total_failed_dequeues = 0
        self.lock = threading.RLock()
        
    def enqueue(self, data) -> bool:
        """Enqueue data."""
        try:
            with self.lock:
                self.queue.put_nowait(data)
                self.total_enqueued += 1
                return True
        except queue.Full:
            with self.lock:
                self.total_failed_enqueues += 1
            return False
            
    def dequeue(self):
        """Dequeue data."""
        try:
            with self.lock:
                data = self.queue.get_nowait()
                self.total_dequeued += 1
                return data
        except queue.Empty:
            with self.lock:
                self.total_failed_dequeues += 1
            return None
            
    def enqueue_packet(self, packet_data) -> bool:
        """Enqueue packet data."""
        return self.enqueue(packet_data)
        
    def dequeue_packet(self):
        """Dequeue packet data."""
        return self.dequeue()
        
    def enqueue_message(self, message) -> bool:
        """Enqueue message."""
        return self.enqueue(message)
        
    def dequeue_message(self):
        """Dequeue message."""
        return self.dequeue()
        
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self.queue.empty()
        
    def is_full(self) -> bool:
        """Check if queue is full."""
        return self.queue.full()
        
    def size(self) -> int:
        """Get queue size."""
        return self.queue.qsize()
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics."""
        with self.lock:
            return {
                'capacity': self.capacity,
                'size': self.size(),
                'capacity_remaining': self.capacity - self.size(),
                'total_enqueued': self.total_enqueued,
                'total_dequeued': self.total_dequeued,
                'total_failed_enqueues': self.total_failed_enqueues,
                'total_failed_dequeues': self.total_failed_dequeues,
                'enqueue_success_rate': (
                    self.total_enqueued / max(1, self.total_enqueued + self.total_failed_enqueues)
                ) * 100.0,
                'dequeue_success_rate': (
                    self.total_dequeued / max(1, self.total_dequeued + self.total_failed_dequeues)
                ) * 100.0,
                'is_empty': self.is_empty(),
                'is_full': self.is_full(),
            }
            
    def clear(self):
        """Clear the queue."""
        with self.lock:
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    break
                    
    def get_capacity(self) -> int:
        """Get queue capacity."""
        return self.capacity 