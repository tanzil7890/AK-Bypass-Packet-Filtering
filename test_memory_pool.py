#!/usr/bin/env python3
"""
High-Performance Memory Pool Test

Test script to verify the Cython-optimized memory pool functionality.
"""

import time
import sys
from hft_packetfilter.core.c_extensions import HighPerformanceMemoryPool, EXTENSIONS_AVAILABLE

def test_memory_pool():
    """Comprehensive memory pool test."""
    print("🧪 Testing High-Performance Memory Pool")
    print("=" * 50)
    
    if not EXTENSIONS_AVAILABLE:
        print("❌ C extensions not available - using fallback")
        return False
    
    print("✅ C extensions available - testing optimized implementation")
    
    # Test 1: Basic allocation and deallocation
    print("\n1. Testing basic allocation/deallocation...")
    pool = HighPerformanceMemoryPool(pool_size=64*1024, block_size=1024)  # 64KB pool
    
    buffer = pool.allocate()
    if buffer is None:
        print("❌ Failed to allocate memory")
        return False
    
    print(f"✅ Allocated buffer: {len(buffer)} bytes")
    
    # Test writing to buffer
    buffer[0] = 0xFF
    buffer[100] = 0xAA
    buffer[1023] = 0x55
    
    if buffer[0] != 0xFF or buffer[100] != 0xAA or buffer[1023] != 0x55:
        print("❌ Buffer write/read test failed")
        return False
    
    print("✅ Buffer write/read test passed")
    
    pool.deallocate(buffer)
    print("✅ Buffer deallocated successfully")
    
    # Test 2: Multiple allocations
    print("\n2. Testing multiple allocations...")
    buffers = []
    for i in range(10):
        buf = pool.allocate()
        if buf is None:
            print(f"❌ Failed to allocate buffer {i}")
            return False
        buffers.append(buf)
    
    print(f"✅ Allocated {len(buffers)} buffers successfully")
    
    # Deallocate all buffers
    for buf in buffers:
        pool.deallocate(buf)
    
    print("✅ All buffers deallocated successfully")
    
    # Test 3: Statistics
    print("\n3. Testing statistics...")
    stats = pool.get_statistics()
    expected_keys = ['pool_size_bytes', 'block_size_bytes', 'total_blocks', 
                     'blocks_allocated', 'blocks_free', 'utilization_percent',
                     'total_allocations', 'total_deallocations', 'use_mmap']
    
    for key in expected_keys:
        if key not in stats:
            print(f"❌ Missing statistic: {key}")
            return False
    
    print("✅ All statistics available")
    print(f"   Pool size: {stats['pool_size_bytes']} bytes")
    print(f"   Block size: {stats['block_size_bytes']} bytes")
    print(f"   Total blocks: {stats['total_blocks']}")
    print(f"   Blocks allocated: {stats['blocks_allocated']}")
    print(f"   Blocks free: {stats['blocks_free']}")
    print(f"   Utilization: {stats['utilization_percent']:.1f}%")
    print(f"   Total allocations: {stats['total_allocations']}")
    print(f"   Total deallocations: {stats['total_deallocations']}")
    
    # Test 4: Specialized allocations
    print("\n4. Testing specialized allocations...")
    packet_buffer = pool.allocate_packet_buffer()
    message_buffer = pool.allocate_message_buffer()
    
    if packet_buffer is None or message_buffer is None:
        print("❌ Failed to allocate specialized buffers")
        return False
    
    print("✅ Packet and message buffers allocated")
    
    pool.deallocate(packet_buffer)
    pool.deallocate(message_buffer)
    print("✅ Specialized buffers deallocated")
    
    # Test 5: Pool exhaustion
    print("\n5. Testing pool exhaustion...")
    total_blocks = stats['total_blocks']
    exhaustion_buffers = []
    
    # Allocate all blocks
    for i in range(total_blocks):
        buf = pool.allocate()
        if buf is None:
            break
        exhaustion_buffers.append(buf)
    
    # Try to allocate one more (should fail)
    extra_buffer = pool.allocate()
    if extra_buffer is not None:
        print("❌ Pool should be exhausted but allocation succeeded")
        return False
    
    print(f"✅ Pool exhaustion test passed ({len(exhaustion_buffers)} blocks allocated)")
    
    # Clean up
    for buf in exhaustion_buffers:
        pool.deallocate(buf)
    
    # Test 6: Performance test
    print("\n6. Testing performance...")
    start_time = time.time()
    num_operations = 10000
    
    for i in range(num_operations):
        buf = pool.allocate()
        if buf is not None:
            buf[0] = i & 0xFF  # Write test
            pool.deallocate(buf)
    
    end_time = time.time()
    duration = end_time - start_time
    ops_per_second = num_operations / duration
    
    print(f"✅ Performance test completed")
    print(f"   Operations: {num_operations}")
    print(f"   Duration: {duration:.3f} seconds")
    print(f"   Rate: {ops_per_second:.0f} operations/second")
    
    # Test 7: Reset pool
    print("\n7. Testing pool reset...")
    # Allocate some buffers
    reset_buffers = [pool.allocate() for _ in range(5)]
    
    stats_before = pool.get_statistics()
    pool.reset_pool()
    stats_after = pool.get_statistics()
    
    if stats_after['blocks_allocated'] != 0:
        print("❌ Pool reset failed - blocks still allocated")
        return False
    
    print("✅ Pool reset successful")
    print(f"   Before reset: {stats_before['blocks_allocated']} allocated")
    print(f"   After reset: {stats_after['blocks_allocated']} allocated")
    
    # Test 8: Memory prefaulting
    print("\n8. Testing memory prefaulting...")
    pool.prefault_memory()
    print("✅ Memory prefaulting completed")
    
    print("\n🎉 All memory pool tests passed!")
    return True

def benchmark_memory_pool():
    """Benchmark memory pool performance."""
    print("\n🚀 Memory Pool Performance Benchmark")
    print("=" * 50)
    
    pool = HighPerformanceMemoryPool(pool_size=1024*1024, block_size=1024)  # 1MB pool
    
    # Warm up
    for _ in range(1000):
        buf = pool.allocate()
        if buf:
            pool.deallocate(buf)
    
    # Benchmark pure allocation/deallocation
    num_iterations = 100000
    start_time = time.time()
    
    for _ in range(num_iterations):
        buf = pool.allocate()
        if buf:
            pool.deallocate(buf)
    
    end_time = time.time()
    duration = end_time - start_time
    rate = num_iterations / duration
    
    print(f"Allocation/Deallocation Rate: {rate:.0f} ops/sec")
    print(f"Average latency: {(duration / num_iterations) * 1_000_000:.2f} microseconds")
    
    # Benchmark with memory access
    start_time = time.time()
    
    for i in range(num_iterations // 10):  # Fewer iterations for memory access test
        buf = pool.allocate()
        if buf:
            # Write pattern to entire buffer
            for j in range(0, len(buf), 64):  # Every cache line
                buf[j] = (i + j) & 0xFF
            pool.deallocate(buf)
    
    end_time = time.time()
    duration = end_time - start_time
    rate = (num_iterations // 10) / duration
    
    print(f"With memory access: {rate:.0f} ops/sec")
    
    stats = pool.get_statistics()
    print(f"\nFinal statistics:")
    print(f"  Total allocations: {stats['total_allocations']}")
    print(f"  Total deallocations: {stats['total_deallocations']}")

if __name__ == "__main__":
    success = test_memory_pool()
    
    if success:
        benchmark_memory_pool()
        print("\n✅ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1) 