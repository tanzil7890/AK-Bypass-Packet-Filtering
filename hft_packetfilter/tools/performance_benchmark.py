#!/usr/bin/env python3
"""
Performance Benchmark Tool

Comprehensive benchmarking suite for HFT packet filtering performance.
Tests C extensions vs Python fallbacks and provides detailed metrics.

Author: HFT-PacketFilter Development Team
License: Apache License 2.0
"""

import time
import random
import statistics
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import gc
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
import warnings

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from hft_packetfilter.core.c_extensions import (
        FastPacketParser,
        UltraLowLatencyTracker,
        HighPerformanceMemoryPool,
        LockFreeQueue,
        EXTENSIONS_AVAILABLE
    )
    
    # Import fallbacks for comparison
    from hft_packetfilter.core.c_extensions.fallbacks import (
        FastPacketParser as PythonPacketParser,
        UltraLowLatencyTracker as PythonLatencyTracker,
        HighPerformanceMemoryPool as PythonMemoryPool,
        LockFreeQueue as PythonQueue,
    )
    
    from hft_packetfilter.core.c_extensions.performance_utils import (
        get_performance_info,
        setup_hft_optimizations,
        validate_hft_environment
    )
    
except ImportError as e:
    print(f"Warning: Could not import HFT modules: {e}")
    print("Please ensure the package is properly installed.")
    sys.exit(1)

class PerformanceBenchmark:
    """Comprehensive performance benchmarking suite."""
    
    def __init__(self, warmup_iterations: int = 1000, test_iterations: int = 10000):
        self.warmup_iterations = warmup_iterations
        self.test_iterations = test_iterations
        self.results = {}
        
        # Generate test data
        self.test_packets = self._generate_test_packets()
        self.test_latencies = self._generate_test_latencies()
        
        print(f"Performance Benchmark initialized:")
        print(f"  - C Extensions Available: {EXTENSIONS_AVAILABLE}")
        print(f"  - Warmup iterations: {warmup_iterations:,}")
        print(f"  - Test iterations: {test_iterations:,}")
        print(f"  - Test packets generated: {len(self.test_packets):,}")
        print()
        
    def _generate_test_packets(self) -> List[bytes]:
        """Generate realistic test packet data."""
        packets = []
        
        # Generate various packet types
        for _ in range(1000):
            # Ethernet header
            eth_header = bytearray(14)
            eth_header[12:14] = (0x08, 0x00)  # IPv4
            
            # IPv4 header
            ip_header = bytearray(20)
            ip_header[0] = 0x45  # Version 4, header length 5
            ip_header[9] = random.choice([6, 17])  # TCP or UDP
            ip_header[12:16] = random.randbytes(4)  # Source IP
            ip_header[16:20] = random.randbytes(4)  # Dest IP
            
            if ip_header[9] == 6:  # TCP
                # TCP header
                tcp_header = bytearray(20)
                # Exchange ports
                src_port = random.choice([4001, 4002, 4003, 9001, 9002, 9003])
                dest_port = random.choice([4001, 4002, 4003, 9001, 9002, 9003])
                tcp_header[0:2] = src_port.to_bytes(2, 'big')
                tcp_header[2:4] = dest_port.to_bytes(2, 'big')
                tcp_header[12] = 0x50  # Header length
                
                # FIX message payload (sometimes)
                payload = b""
                if random.random() < 0.3:  # 30% FIX messages
                    payload = b"8=FIX.4.4\x019=154\x0135=D\x0149=SENDER\x0156=TARGET\x01"
                    
                packet = eth_header + ip_header + tcp_header + payload
                
            else:  # UDP
                # UDP header
                udp_header = bytearray(8)
                src_port = random.choice([4001, 4002, 4003, 9001, 9002, 9003])
                dest_port = random.choice([4001, 4002, 4003, 9001, 9002, 9003])
                udp_header[0:2] = src_port.to_bytes(2, 'big')
                udp_header[2:4] = dest_port.to_bytes(2, 'big')
                udp_header[4:6] = (8 + 100).to_bytes(2, 'big')  # Length
                
                # Market data payload
                payload = random.randbytes(100)
                packet = eth_header + ip_header + udp_header + payload
                
            packets.append(bytes(packet))
            
        return packets
        
    def _generate_test_latencies(self) -> List[float]:
        """Generate realistic latency test data."""
        latencies = []
        
        # Normal trading latencies (400-600μs with some outliers)
        for _ in range(1000):
            if random.random() < 0.95:  # 95% normal
                latency = random.gauss(500, 50)  # Normal around 500μs
            else:  # 5% outliers
                latency = random.gauss(2000, 500)  # Spike to ~2ms
                
            latencies.append(max(50, latency))  # Minimum 50μs
            
        return latencies
        
    def benchmark_packet_parsing(self) -> Dict[str, Any]:
        """Benchmark packet parsing performance."""
        print("🔍 Benchmarking Packet Parsing...")
        
        results = {}
        
        # Benchmark C extension (if available)
        if EXTENSIONS_AVAILABLE:
            print("  Testing C extension...")
            parser = FastPacketParser()
            
            # Warmup
            for packet in self.test_packets[:self.warmup_iterations // 10]:
                parser.parse_packet_fast(np.frombuffer(packet, dtype=np.uint8))
                
            # Benchmark
            start_time = time.perf_counter()
            parsed_count = 0
            
            for _ in range(self.test_iterations):
                packet = random.choice(self.test_packets)
                result = parser.parse_packet_fast(np.frombuffer(packet, dtype=np.uint8))
                if result:
                    parsed_count += 1
                    
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            results['c_extension'] = {
                'duration_seconds': duration,
                'packets_per_second': self.test_iterations / duration,
                'parsed_packets': parsed_count,
                'parse_rate': parsed_count / self.test_iterations,
                'avg_time_per_packet_ns': (duration / self.test_iterations) * 1e9,
                'statistics': parser.get_statistics()
            }
            
        # Benchmark Python fallback
        print("  Testing Python fallback...")
        parser_py = PythonPacketParser()
        
        # Warmup
        for packet in self.test_packets[:self.warmup_iterations // 10]:
            parser_py.parse_packet_fast(packet)
            
        # Benchmark
        start_time = time.perf_counter()
        parsed_count = 0
        
        for _ in range(self.test_iterations):
            packet = random.choice(self.test_packets)
            result = parser_py.parse_packet_fast(packet)
            if result:
                parsed_count += 1
                
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        results['python_fallback'] = {
            'duration_seconds': duration,
            'packets_per_second': self.test_iterations / duration,
            'parsed_packets': parsed_count,
            'parse_rate': parsed_count / self.test_iterations,
            'avg_time_per_packet_ns': (duration / self.test_iterations) * 1e9,
            'statistics': parser_py.get_statistics()
        }
        
        # Calculate performance improvement
        if EXTENSIONS_AVAILABLE and 'c_extension' in results:
            speedup = (results['python_fallback']['packets_per_second'] / 
                      results['c_extension']['packets_per_second'])
            results['performance_improvement'] = {
                'speedup_factor': speedup,
                'latency_reduction_ns': (
                    results['python_fallback']['avg_time_per_packet_ns'] - 
                    results['c_extension']['avg_time_per_packet_ns']
                )
            }
            
        return results
        
    def benchmark_latency_tracking(self) -> Dict[str, Any]:
        """Benchmark latency tracking performance."""
        print("⏱️  Benchmarking Latency Tracking...")
        
        results = {}
        
        # Benchmark C extension (if available)
        if EXTENSIONS_AVAILABLE:
            print("  Testing C extension...")
            tracker = UltraLowLatencyTracker(max_samples=50000, target_latency_us=500.0)
            
            # Warmup
            for latency in self.test_latencies[:self.warmup_iterations // 10]:
                tracker.record_latency(latency, random.randint(1, 3), 'TCP')
                
            # Benchmark
            start_time = time.perf_counter()
            
            for _ in range(self.test_iterations):
                latency = random.choice(self.test_latencies)
                tracker.record_latency(latency, random.randint(1, 3), 'TCP')
                
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            # Get statistics
            stats = tracker.get_statistics()
            
            results['c_extension'] = {
                'duration_seconds': duration,
                'recordings_per_second': self.test_iterations / duration,
                'avg_time_per_recording_ns': (duration / self.test_iterations) * 1e9,
                'statistics': stats
            }
            
        # Benchmark Python fallback
        print("  Testing Python fallback...")
        tracker_py = PythonLatencyTracker(max_samples=50000, target_latency_us=500.0)
        
        # Warmup
        for latency in self.test_latencies[:self.warmup_iterations // 10]:
            tracker_py.record_latency(latency, random.randint(1, 3), 'TCP')
            
        # Benchmark
        start_time = time.perf_counter()
        
        for _ in range(self.test_iterations):
            latency = random.choice(self.test_latencies)
            tracker_py.record_latency(latency, random.randint(1, 3), 'TCP')
            
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # Get statistics
        stats = tracker_py.get_statistics()
        
        results['python_fallback'] = {
            'duration_seconds': duration,
            'recordings_per_second': self.test_iterations / duration,
            'avg_time_per_recording_ns': (duration / self.test_iterations) * 1e9,
            'statistics': stats
        }
        
        # Calculate performance improvement
        if EXTENSIONS_AVAILABLE and 'c_extension' in results:
            speedup = (results['c_extension']['recordings_per_second'] / 
                      results['python_fallback']['recordings_per_second'])
            results['performance_improvement'] = {
                'speedup_factor': speedup,
                'latency_reduction_ns': (
                    results['python_fallback']['avg_time_per_recording_ns'] - 
                    results['c_extension']['avg_time_per_recording_ns']
                )
            }
            
        return results
        
    def benchmark_memory_pool(self) -> Dict[str, Any]:
        """Benchmark memory pool performance."""
        print("💾 Benchmarking Memory Pool...")
        
        results = {}
        
        # Benchmark C extension (if available)
        if EXTENSIONS_AVAILABLE:
            print("  Testing C extension...")
            pool = HighPerformanceMemoryPool(pool_size=1024*1024, block_size=1024)
            pool.prefault_memory()
            
            # Warmup
            buffers = []
            for _ in range(self.warmup_iterations // 100):
                buf = pool.allocate()
                if buf:
                    buffers.append(buf)
            for buf in buffers:
                pool.deallocate(buf)
                
            # Benchmark allocation
            start_time = time.perf_counter()
            allocated_buffers = []
            
            for _ in range(self.test_iterations // 10):
                buf = pool.allocate()
                if buf:
                    allocated_buffers.append(buf)
                    
            alloc_time = time.perf_counter() - start_time
            
            # Benchmark deallocation
            start_time = time.perf_counter()
            
            for buf in allocated_buffers:
                pool.deallocate(buf)
                
            dealloc_time = time.perf_counter() - start_time
            
            results['c_extension'] = {
                'alloc_duration_seconds': alloc_time,
                'dealloc_duration_seconds': dealloc_time,
                'allocations_per_second': len(allocated_buffers) / alloc_time,
                'deallocations_per_second': len(allocated_buffers) / dealloc_time,
                'avg_alloc_time_ns': (alloc_time / len(allocated_buffers)) * 1e9,
                'avg_dealloc_time_ns': (dealloc_time / len(allocated_buffers)) * 1e9,
                'statistics': pool.get_statistics()
            }
            
        # Benchmark Python fallback
        print("  Testing Python fallback...")
        pool_py = PythonMemoryPool(pool_size=1024*1024, block_size=1024)
        
        # Warmup
        buffers = []
        for _ in range(self.warmup_iterations // 100):
            buf = pool_py.allocate()
            if buf:
                buffers.append(buf)
        for buf in buffers:
            pool_py.deallocate(buf)
            
        # Benchmark allocation
        start_time = time.perf_counter()
        allocated_buffers = []
        
        for _ in range(self.test_iterations // 10):
            buf = pool_py.allocate()
            if buf:
                allocated_buffers.append(buf)
                
        alloc_time = time.perf_counter() - start_time
        
        # Benchmark deallocation
        start_time = time.perf_counter()
        
        for buf in allocated_buffers:
            pool_py.deallocate(buf)
            
        dealloc_time = time.perf_counter() - start_time
        
        results['python_fallback'] = {
            'alloc_duration_seconds': alloc_time,
            'dealloc_duration_seconds': dealloc_time,
            'allocations_per_second': len(allocated_buffers) / alloc_time,
            'deallocations_per_second': len(allocated_buffers) / dealloc_time,
            'avg_alloc_time_ns': (alloc_time / len(allocated_buffers)) * 1e9,
            'avg_dealloc_time_ns': (dealloc_time / len(allocated_buffers)) * 1e9,
            'statistics': pool_py.get_statistics()
        }
        
        # Calculate performance improvement
        if EXTENSIONS_AVAILABLE and 'c_extension' in results:
            alloc_speedup = (results['c_extension']['allocations_per_second'] / 
                           results['python_fallback']['allocations_per_second'])
            dealloc_speedup = (results['c_extension']['deallocations_per_second'] / 
                             results['python_fallback']['deallocations_per_second'])
            
            results['performance_improvement'] = {
                'alloc_speedup_factor': alloc_speedup,
                'dealloc_speedup_factor': dealloc_speedup,
                'avg_speedup_factor': (alloc_speedup + dealloc_speedup) / 2
            }
            
        return results
        
    def benchmark_lock_free_queue(self) -> Dict[str, Any]:
        """Benchmark lock-free queue performance."""
        print("🔀 Benchmarking Lock-Free Queue...")
        
        results = {}
        test_data = [f"message_{i}" for i in range(1000)]
        
        # Benchmark C extension (if available)
        if EXTENSIONS_AVAILABLE:
            print("  Testing C extension...")
            queue = LockFreeQueue(capacity=32768)
            
            # Single-threaded benchmark
            start_time = time.perf_counter()
            
            for _ in range(self.test_iterations // 10):
                data = random.choice(test_data)
                queue.enqueue(data)
                
            enqueue_time = time.perf_counter() - start_time
            
            start_time = time.perf_counter()
            dequeued_count = 0
            
            while not queue.is_empty():
                if queue.dequeue():
                    dequeued_count += 1
                    
            dequeue_time = time.perf_counter() - start_time
            
            results['c_extension'] = {
                'enqueue_duration_seconds': enqueue_time,
                'dequeue_duration_seconds': dequeue_time,
                'enqueues_per_second': (self.test_iterations // 10) / enqueue_time,
                'dequeues_per_second': dequeued_count / dequeue_time,
                'statistics': queue.get_statistics()
            }
            
        # Benchmark Python fallback
        print("  Testing Python fallback...")
        queue_py = PythonQueue(capacity=32768)
        
        # Single-threaded benchmark
        start_time = time.perf_counter()
        
        for _ in range(self.test_iterations // 10):
            data = random.choice(test_data)
            queue_py.enqueue(data)
            
        enqueue_time = time.perf_counter() - start_time
        
        start_time = time.perf_counter()
        dequeued_count = 0
        
        while not queue_py.is_empty():
            if queue_py.dequeue():
                dequeued_count += 1
                
        dequeue_time = time.perf_counter() - start_time
        
        results['python_fallback'] = {
            'enqueue_duration_seconds': enqueue_time,
            'dequeue_duration_seconds': dequeue_time,
            'enqueues_per_second': (self.test_iterations // 10) / enqueue_time,
            'dequeues_per_second': dequeued_count / dequeue_time,
            'statistics': queue_py.get_statistics()
        }
        
        # Calculate performance improvement
        if EXTENSIONS_AVAILABLE and 'c_extension' in results:
            enqueue_speedup = (results['c_extension']['enqueues_per_second'] / 
                             results['python_fallback']['enqueues_per_second'])
            dequeue_speedup = (results['c_extension']['dequeues_per_second'] / 
                             results['python_fallback']['dequeues_per_second'])
            
            results['performance_improvement'] = {
                'enqueue_speedup_factor': enqueue_speedup,
                'dequeue_speedup_factor': dequeue_speedup,
                'avg_speedup_factor': (enqueue_speedup + dequeue_speedup) / 2
            }
            
        return results
        
    def run_full_benchmark(self) -> Dict[str, Any]:
        """Run complete performance benchmark suite."""
        print("🚀 Starting Full Performance Benchmark Suite")
        print("=" * 60)
        
        # System information
        perf_info = get_performance_info()
        hft_validation = validate_hft_environment()
        
        print(f"System Information:")
        print(f"  Platform: {perf_info['platform']} {perf_info['architecture']}")
        print(f"  CPU Cores: {perf_info['cpu_count_physical']} physical, {perf_info['cpu_count_logical']} logical")
        print(f"  Memory: {perf_info['memory_available_gb']:.1f}GB available")
        print(f"  Cache Line Size: {perf_info['cache_line_size']} bytes")
        print(f"  HFT Suitable: {hft_validation['suitable_for_hft']}")
        print()
        
        # Run individual benchmarks
        results = {
            'system_info': perf_info,
            'hft_validation': hft_validation,
            'packet_parsing': self.benchmark_packet_parsing(),
            'latency_tracking': self.benchmark_latency_tracking(),
            'memory_pool': self.benchmark_memory_pool(),
            'lock_free_queue': self.benchmark_lock_free_queue(),
        }
        
        # Generate summary
        results['summary'] = self._generate_summary(results)
        
        return results
        
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance summary."""
        summary = {
            'extensions_available': EXTENSIONS_AVAILABLE,
            'overall_performance_gain': 'N/A',
            'recommendations': []
        }
        
        if not EXTENSIONS_AVAILABLE:
            summary['recommendations'].append("Install C extensions for significant performance improvements")
            return summary
            
        # Calculate overall performance gains
        speedups = []
        
        for benchmark in ['packet_parsing', 'latency_tracking', 'memory_pool', 'lock_free_queue']:
            if benchmark in results and 'performance_improvement' in results[benchmark]:
                perf_data = results[benchmark]['performance_improvement']
                
                if 'speedup_factor' in perf_data:
                    speedups.append(perf_data['speedup_factor'])
                elif 'avg_speedup_factor' in perf_data:
                    speedups.append(perf_data['avg_speedup_factor'])
                    
        if speedups:
            avg_speedup = statistics.mean(speedups)
            summary['overall_performance_gain'] = f"{avg_speedup:.1f}x faster"
            summary['individual_speedups'] = {
                'packet_parsing': results.get('packet_parsing', {}).get('performance_improvement', {}).get('speedup_factor', 'N/A'),
                'latency_tracking': results.get('latency_tracking', {}).get('performance_improvement', {}).get('speedup_factor', 'N/A'),
                'memory_pool': results.get('memory_pool', {}).get('performance_improvement', {}).get('avg_speedup_factor', 'N/A'),
                'lock_free_queue': results.get('lock_free_queue', {}).get('performance_improvement', {}).get('avg_speedup_factor', 'N/A'),
            }
            
            # Performance recommendations
            if avg_speedup > 5:
                summary['recommendations'].append("Excellent performance gains achieved with C extensions")
            elif avg_speedup > 2:
                summary['recommendations'].append("Good performance gains with C extensions")
            else:
                summary['recommendations'].append("Consider system-level optimizations for better performance")
                
        return summary
        
    def print_results(self, results: Dict[str, Any]):
        """Print formatted benchmark results."""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE BENCHMARK RESULTS")
        print("=" * 60)
        
        summary = results.get('summary', {})
        print(f"\n🎯 Overall Performance: {summary.get('overall_performance_gain', 'N/A')}")
        print(f"🔧 C Extensions: {'✅ Available' if summary.get('extensions_available') else '❌ Not Available'}")
        
        if 'individual_speedups' in summary:
            print(f"\n📈 Individual Speedups:")
            for component, speedup in summary['individual_speedups'].items():
                if isinstance(speedup, (int, float)):
                    print(f"  {component.replace('_', ' ').title()}: {speedup:.1f}x")
                else:
                    print(f"  {component.replace('_', ' ').title()}: {speedup}")
                    
        print(f"\n💡 Recommendations:")
        for rec in summary.get('recommendations', []):
            print(f"  • {rec}")
            
        # Detailed results for each benchmark
        benchmarks = ['packet_parsing', 'latency_tracking', 'memory_pool', 'lock_free_queue']
        
        for benchmark in benchmarks:
            if benchmark not in results:
                continue
                
            print(f"\n{benchmark.replace('_', ' ').title()} Results:")
            bench_data = results[benchmark]
            
            if 'c_extension' in bench_data:
                print("  C Extension:")
                self._print_benchmark_details(bench_data['c_extension'])
                
            if 'python_fallback' in bench_data:
                print("  Python Fallback:")
                self._print_benchmark_details(bench_data['python_fallback'])
                
    def _print_benchmark_details(self, data: Dict[str, Any]):
        """Print detailed benchmark metrics."""
        if 'packets_per_second' in data:
            print(f"    Packets/sec: {data['packets_per_second']:,.0f}")
        if 'recordings_per_second' in data:
            print(f"    Recordings/sec: {data['recordings_per_second']:,.0f}")
        if 'allocations_per_second' in data:
            print(f"    Allocations/sec: {data['allocations_per_second']:,.0f}")
        if 'enqueues_per_second' in data:
            print(f"    Enqueues/sec: {data['enqueues_per_second']:,.0f}")
        if 'avg_time_per_packet_ns' in data:
            print(f"    Avg time/packet: {data['avg_time_per_packet_ns']:.1f}ns")


def main():
    """Main benchmark execution."""
    print("🔥 HFT-PacketFilter Performance Benchmark")
    print("Testing C extensions vs Python fallbacks")
    print()
    
    # Setup HFT optimizations
    print("⚙️  Setting up HFT optimizations...")
    opt_results = setup_hft_optimizations(thread_priority="high")
    for opt, success in opt_results.items():
        status = "✅" if success else "❌"
        print(f"  {opt.replace('_', ' ').title()}: {status}")
    print()
    
    # Run benchmark
    benchmark = PerformanceBenchmark(warmup_iterations=1000, test_iterations=50000)
    results = benchmark.run_full_benchmark()
    benchmark.print_results(results)
    
    print(f"\n{'='*60}")
    print("✨ Benchmark completed successfully!")


if __name__ == "__main__":
    main() 