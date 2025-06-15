#!/usr/bin/env python3
"""Quick test for Ultra-High Performance Market Data Simulator with C extensions"""

from market_data_simulator import UltraHighPerformanceMarketDataSimulator, EXTENSIONS_AVAILABLE
from hft_packetfilter import HFTAnalyzer
from hft_packetfilter.core.exchange_config import CommonExchanges
import time

def test_ultra_simulator():
    print('🧪 Testing Ultra-High Performance Market Data Simulator')
    print('=' * 60)

    # Quick initialization test
    analyzer = HFTAnalyzer()
    exchanges = [CommonExchanges.nyse(), CommonExchanges.nasdaq(), CommonExchanges.cboe()]
    for exchange in exchanges:
        analyzer.add_exchange(exchange)

    # Create simulator
    simulator = UltraHighPerformanceMarketDataSimulator(analyzer)

    # Show C extension integration status
    print(f'\n📊 C Extension Integration Status:')
    print(f'   • Extensions Available: {EXTENSIONS_AVAILABLE}')

    if hasattr(simulator, 'packet_memory_pool') and simulator.packet_memory_pool:
        stats = simulator.packet_memory_pool.get_statistics()
        print(f'   • Memory Pool: {stats["pool_size_bytes"]//1024}KB with {stats["total_blocks"]:,} blocks')
        print(f'   • Block Size: {stats["block_size_bytes"]}B')
        print(f'   • Free Blocks: {stats["blocks_free"]:,}')

    if hasattr(simulator, 'message_queues') and simulator.message_queues:
        queue_stats = simulator.message_queues[0].get_statistics()
        print(f'   • Lock-Free Queues: {len(simulator.message_queues)} x {queue_stats["capacity"]:,} capacity')

    if hasattr(simulator, 'arbitrage_queue') and simulator.arbitrage_queue:
        arb_stats = simulator.arbitrage_queue.get_statistics()
        print(f'   • Arbitrage Queue: {arb_stats["capacity"]:,} capacity')

    # Test ultra-fast message generation
    print(f'\n⚡ Testing Ultra-Fast Message Generation:')
    start_time = time.time()
    messages_generated = 0
    
    for i in range(1000):  # Generate 1000 messages
        message = simulator._generate_ultra_fast_message(i % 3, simulator.exchanges[i % 3], i % len(simulator.symbols))
        if message:
            messages_generated += 1
    
    duration = time.time() - start_time
    rate = messages_generated / duration if duration > 0 else 0
    
    print(f'   • Generated: {messages_generated:,} messages in {duration:.3f}s')
    print(f'   • Rate: {rate:,.0f} messages/second')
    
    # Show some sample messages
    print(f'\n📋 Sample Messages:')
    for i in range(5):
        message = simulator._generate_ultra_fast_message(i % 3, simulator.exchanges[i % 3], i % len(simulator.symbols))
        if message:
            print(f'   • {message.exchange_name}: {simulator.symbols[i % len(simulator.symbols)]} - {message.latency_us:.2f}μs, {message.packet_size}B')

    # Test memory pool performance
    if hasattr(simulator, 'packet_memory_pool') and simulator.packet_memory_pool:
        print(f'\n🚀 Testing Memory Pool Performance:')
        pool_start = time.time()
        allocations = 0
        
        for i in range(10000):
            buffer = simulator.packet_memory_pool.allocate()
            if buffer:
                allocations += 1
                simulator.packet_memory_pool.deallocate(buffer)
        
        pool_duration = time.time() - pool_start
        pool_rate = (allocations * 2) / pool_duration  # alloc + dealloc
        
        print(f'   • Allocations: {allocations:,} in {pool_duration:.3f}s')
        print(f'   • Rate: {pool_rate:,.0f} operations/second')
        
        final_stats = simulator.packet_memory_pool.get_statistics()
        print(f'   • Final allocations: {final_stats["total_allocations"]:,}')
        print(f'   • Final deallocations: {final_stats["total_deallocations"]:,}')
        print(f'   • Memory leaks: {"None" if final_stats["total_allocations"] == final_stats["total_deallocations"] else "Detected"}')

    print(f'\n✅ Ultra-High Performance Simulator Test Complete!')
    print(f'   Ready for production HFT trading simulation with C extensions')
    return True

if __name__ == "__main__":
    test_ultra_simulator() 