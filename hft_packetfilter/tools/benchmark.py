#!/usr/bin/env python3
"""
HFT Benchmark - Performance Testing CLI Tool

Command-line interface for benchmarking HFT-PacketFilter performance,
measuring latency, throughput, and system resource usage.

Author: Tanzil github://@tanzil7890
License: Apache License 2.0
"""

import click
import time
import statistics
import psutil
import json
from typing import List, Dict, Any
from datetime import datetime

from ..core.hft_analyzer import HFTAnalyzer
from ..core.exchange_config import CommonExchanges
from ..core.production_config import ProductionConfig
from ..utils.logger import HFTLogger


@click.command()
@click.option('--duration', '-d', type=int, default=60,
              help='Benchmark duration in seconds')
@click.option('--performance-mode', '-p', 
              type=click.Choice(['standard', 'high_performance', 'ultra_low_latency']),
              default='standard', help='Performance mode to test')
@click.option('--output', '-o', type=click.Path(),
              help='Output file for benchmark results')
@click.option('--format', type=click.Choice(['json', 'csv', 'console']),
              default='console', help='Output format')
@click.option('--test-type', '-t', 
              type=click.Choice(['latency', 'throughput', 'memory', 'cpu', 'all']),
              multiple=True, default=['all'], help='Types of benchmarks to run')
@click.option('--exchanges', '-e', type=int, default=2,
              help='Number of exchanges to simulate')
@click.option('--packet-rate', type=int, default=1000,
              help='Simulated packet rate per second')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose output')
def main(duration: int, performance_mode: str, output: str, format: str,
         test_type: tuple, exchanges: int, packet_rate: int, verbose: bool):
    """
    HFT Benchmark - Performance Testing for HFT-PacketFilter
    
    Run comprehensive performance benchmarks to measure latency, throughput,
    memory usage, and CPU utilization under various load conditions.
    
    Examples:
        hft-benchmark --duration 300 --performance-mode ultra_low_latency
        hft-benchmark --test-type latency --test-type throughput --output results.json
        hft-benchmark --exchanges 5 --packet-rate 10000 --verbose
    """
    
    # Configure logging
    log_level = "DEBUG" if verbose else "INFO"
    logger = HFTLogger("hft-benchmark", level=log_level)
    
    try:
        # Determine which tests to run
        if 'all' in test_type:
            tests_to_run = ['latency', 'throughput', 'memory', 'cpu']
        else:
            tests_to_run = list(test_type)
        
        click.echo("=" * 60)
        click.echo("HFT-PacketFilter Performance Benchmark")
        click.echo("=" * 60)
        click.echo(f"Duration: {duration}s")
        click.echo(f"Performance Mode: {performance_mode}")
        click.echo(f"Tests: {', '.join(tests_to_run)}")
        click.echo(f"Exchanges: {exchanges}")
        click.echo(f"Packet Rate: {packet_rate}/s")
        click.echo("=" * 60)
        
        # Initialize benchmark environment
        benchmark_results = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': duration,
                'performance_mode': performance_mode,
                'exchanges_count': exchanges,
                'packet_rate': packet_rate,
                'tests_run': tests_to_run
            },
            'system_info': get_system_info(),
            'results': {}
        }
        
        # Run benchmarks
        for test in tests_to_run:
            click.echo(f"\n🔄 Running {test} benchmark...")
            
            if test == 'latency':
                benchmark_results['results']['latency'] = run_latency_benchmark(
                    duration, performance_mode, exchanges, logger
                )
            elif test == 'throughput':
                benchmark_results['results']['throughput'] = run_throughput_benchmark(
                    duration, performance_mode, packet_rate, logger
                )
            elif test == 'memory':
                benchmark_results['results']['memory'] = run_memory_benchmark(
                    duration, performance_mode, logger
                )
            elif test == 'cpu':
                benchmark_results['results']['cpu'] = run_cpu_benchmark(
                    duration, performance_mode, logger
                )
            
            click.echo(f"✅ {test} benchmark completed")
        
        # Generate summary
        summary = generate_benchmark_summary(benchmark_results)
        benchmark_results['summary'] = summary
        
        # Output results
        if output:
            save_benchmark_results(benchmark_results, output, format, logger)
        
        display_benchmark_results(benchmark_results, format)
        
        logger.info("Benchmark completed successfully")
        
    except Exception as e:
        click.echo(f"❌ Benchmark failed: {e}")
        logger.error(f"Benchmark failed: {e}")
        raise click.ClickException(str(e))


def get_system_info() -> Dict[str, Any]:
    """Get system information"""
    
    return {
        'cpu_count': psutil.cpu_count(),
        'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
        'memory_total': psutil.virtual_memory().total,
        'memory_available': psutil.virtual_memory().available,
        'platform': psutil.LINUX if hasattr(psutil, 'LINUX') else 'unknown'
    }


def run_latency_benchmark(duration: int, performance_mode: str, 
                         exchanges: int, logger: HFTLogger) -> Dict[str, Any]:
    """Run latency benchmark"""
    
    # Initialize analyzer
    config = ProductionConfig(performance_mode=performance_mode)
    analyzer = HFTAnalyzer(config=config, performance_mode=performance_mode)
    
    # Add exchanges
    exchange_configs = [CommonExchanges.NYSE(), CommonExchanges.NASDAQ()]
    for i, exchange_config in enumerate(exchange_configs[:exchanges]):
        analyzer.add_exchange(exchange_config)
    
    # Collect latency measurements
    latencies = []
    start_time = time.time()
    
    try:
        analyzer.start_monitoring(duration_seconds=duration)
        
        # Monitor latency during benchmark
        while time.time() - start_time < duration:
            metrics = analyzer.get_live_metrics()
            
            # Extract latency measurements
            for exchange_name, quality_data in metrics.get('market_data_quality', {}).items():
                if 'latency_us' in quality_data:
                    latencies.append(quality_data['latency_us'])
            
            time.sleep(0.1)  # Sample every 100ms
        
    finally:
        analyzer.stop_monitoring()
    
    # Calculate statistics
    if latencies:
        return {
            'total_measurements': len(latencies),
            'min_latency_us': min(latencies),
            'max_latency_us': max(latencies),
            'mean_latency_us': statistics.mean(latencies),
            'median_latency_us': statistics.median(latencies),
            'stdev_latency_us': statistics.stdev(latencies) if len(latencies) > 1 else 0,
            'p95_latency_us': sorted(latencies)[int(len(latencies) * 0.95)],
            'p99_latency_us': sorted(latencies)[int(len(latencies) * 0.99)],
        }
    else:
        return {'error': 'No latency measurements collected'}


def run_throughput_benchmark(duration: int, performance_mode: str, 
                           packet_rate: int, logger: HFTLogger) -> Dict[str, Any]:
    """Run throughput benchmark"""
    
    config = ProductionConfig(performance_mode=performance_mode)
    analyzer = HFTAnalyzer(config=config, performance_mode=performance_mode)
    
    # Add exchanges
    analyzer.add_exchange(CommonExchanges.NYSE())
    analyzer.add_exchange(CommonExchanges.NASDAQ())
    
    packet_counts = []
    start_time = time.time()
    
    try:
        analyzer.start_monitoring(duration_seconds=duration)
        
        # Monitor packet throughput
        last_packet_count = 0
        
        while time.time() - start_time < duration:
            metrics = analyzer.get_live_metrics()
            current_packets = metrics.get('trading_metrics', {}).get('total_packets', 0)
            
            packets_per_second = current_packets - last_packet_count
            packet_counts.append(packets_per_second)
            last_packet_count = current_packets
            
            time.sleep(1.0)  # Sample every second
        
    finally:
        analyzer.stop_monitoring()
    
    if packet_counts:
        return {
            'total_packets': sum(packet_counts),
            'avg_packets_per_second': statistics.mean(packet_counts),
            'max_packets_per_second': max(packet_counts),
            'min_packets_per_second': min(packet_counts),
            'throughput_efficiency': (statistics.mean(packet_counts) / packet_rate) * 100
        }
    else:
        return {'error': 'No throughput measurements collected'}


def run_memory_benchmark(duration: int, performance_mode: str, 
                        logger: HFTLogger) -> Dict[str, Any]:
    """Run memory usage benchmark"""
    
    config = ProductionConfig(performance_mode=performance_mode)
    analyzer = HFTAnalyzer(config=config, performance_mode=performance_mode)
    
    # Add exchanges
    analyzer.add_exchange(CommonExchanges.NYSE())
    analyzer.add_exchange(CommonExchanges.NASDAQ())
    
    memory_usage = []
    start_time = time.time()
    initial_memory = psutil.Process().memory_info().rss
    
    try:
        analyzer.start_monitoring(duration_seconds=duration)
        
        # Monitor memory usage
        while time.time() - start_time < duration:
            current_memory = psutil.Process().memory_info().rss
            memory_usage.append(current_memory)
            time.sleep(1.0)  # Sample every second
        
    finally:
        analyzer.stop_monitoring()
    
    if memory_usage:
        return {
            'initial_memory_mb': initial_memory / (1024 * 1024),
            'peak_memory_mb': max(memory_usage) / (1024 * 1024),
            'avg_memory_mb': statistics.mean(memory_usage) / (1024 * 1024),
            'memory_growth_mb': (max(memory_usage) - initial_memory) / (1024 * 1024),
            'memory_efficiency': 'good' if max(memory_usage) < initial_memory * 2 else 'poor'
        }
    else:
        return {'error': 'No memory measurements collected'}


def run_cpu_benchmark(duration: int, performance_mode: str, 
                     logger: HFTLogger) -> Dict[str, Any]:
    """Run CPU usage benchmark"""
    
    config = ProductionConfig(performance_mode=performance_mode)
    analyzer = HFTAnalyzer(config=config, performance_mode=performance_mode)
    
    # Add exchanges
    analyzer.add_exchange(CommonExchanges.NYSE())
    analyzer.add_exchange(CommonExchanges.NASDAQ())
    
    cpu_usage = []
    start_time = time.time()
    
    try:
        analyzer.start_monitoring(duration_seconds=duration)
        
        # Monitor CPU usage
        while time.time() - start_time < duration:
            cpu_percent = psutil.cpu_percent(interval=1.0)
            cpu_usage.append(cpu_percent)
        
    finally:
        analyzer.stop_monitoring()
    
    if cpu_usage:
        return {
            'avg_cpu_percent': statistics.mean(cpu_usage),
            'max_cpu_percent': max(cpu_usage),
            'min_cpu_percent': min(cpu_usage),
            'cpu_efficiency': 'excellent' if statistics.mean(cpu_usage) < 20 else 
                           'good' if statistics.mean(cpu_usage) < 50 else 'poor'
        }
    else:
        return {'error': 'No CPU measurements collected'}


def generate_benchmark_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate benchmark summary"""
    
    summary = {
        'overall_score': 0,
        'performance_grade': 'Unknown',
        'recommendations': []
    }
    
    scores = []
    
    # Analyze latency results
    if 'latency' in results['results']:
        latency_data = results['results']['latency']
        if 'mean_latency_us' in latency_data:
            # Score based on mean latency (lower is better)
            if latency_data['mean_latency_us'] < 500:
                latency_score = 100
            elif latency_data['mean_latency_us'] < 1000:
                latency_score = 80
            elif latency_data['mean_latency_us'] < 2000:
                latency_score = 60
            else:
                latency_score = 40
            
            scores.append(latency_score)
            
            if latency_data['mean_latency_us'] > 1000:
                summary['recommendations'].append(
                    "Consider optimizing for lower latency - current average exceeds 1ms"
                )
    
    # Analyze throughput results
    if 'throughput' in results['results']:
        throughput_data = results['results']['throughput']
        if 'throughput_efficiency' in throughput_data:
            efficiency = throughput_data['throughput_efficiency']
            if efficiency > 90:
                throughput_score = 100
            elif efficiency > 70:
                throughput_score = 80
            elif efficiency > 50:
                throughput_score = 60
            else:
                throughput_score = 40
            
            scores.append(throughput_score)
            
            if efficiency < 80:
                summary['recommendations'].append(
                    "Throughput efficiency below optimal - consider performance tuning"
                )
    
    # Analyze memory results
    if 'memory' in results['results']:
        memory_data = results['results']['memory']
        if 'memory_efficiency' in memory_data:
            if memory_data['memory_efficiency'] == 'good':
                scores.append(90)
            else:
                scores.append(50)
                summary['recommendations'].append(
                    "High memory usage detected - check for memory leaks"
                )
    
    # Analyze CPU results
    if 'cpu' in results['results']:
        cpu_data = results['results']['cpu']
        if 'cpu_efficiency' in cpu_data:
            if cpu_data['cpu_efficiency'] == 'excellent':
                scores.append(100)
            elif cpu_data['cpu_efficiency'] == 'good':
                scores.append(80)
            else:
                scores.append(50)
                summary['recommendations'].append(
                    "High CPU usage - consider optimizing algorithms"
                )
    
    # Calculate overall score
    if scores:
        summary['overall_score'] = statistics.mean(scores)
        
        if summary['overall_score'] >= 90:
            summary['performance_grade'] = 'A'
        elif summary['overall_score'] >= 80:
            summary['performance_grade'] = 'B'
        elif summary['overall_score'] >= 70:
            summary['performance_grade'] = 'C'
        elif summary['overall_score'] >= 60:
            summary['performance_grade'] = 'D'
        else:
            summary['performance_grade'] = 'F'
    
    return summary


def save_benchmark_results(results: Dict[str, Any], output: str, 
                          format: str, logger: HFTLogger):
    """Save benchmark results to file"""
    
    if format == 'json':
        with open(output, 'w') as f:
            json.dump(results, f, indent=2)
    elif format == 'csv':
        # Convert to CSV format
        import csv
        with open(output, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['metric', 'value', 'unit'])
            
            # Flatten results for CSV
            for test_name, test_results in results['results'].items():
                for metric, value in test_results.items():
                    writer.writerow([f"{test_name}.{metric}", value, ''])
    
    logger.info(f"Benchmark results saved to {output}")


def display_benchmark_results(results: Dict[str, Any], format: str):
    """Display benchmark results"""
    
    if format == 'json':
        click.echo(json.dumps(results, indent=2))
        return
    
    # Console format
    click.echo("\n" + "=" * 60)
    click.echo("BENCHMARK RESULTS")
    click.echo("=" * 60)
    
    # Summary
    summary = results.get('summary', {})
    click.echo(f"\n📊 OVERALL PERFORMANCE")
    click.echo(f"Score: {summary.get('overall_score', 0):.1f}/100")
    click.echo(f"Grade: {summary.get('performance_grade', 'Unknown')}")
    
    # Individual test results
    for test_name, test_results in results['results'].items():
        click.echo(f"\n🔍 {test_name.upper()} RESULTS")
        
        if 'error' in test_results:
            click.echo(f"❌ {test_results['error']}")
            continue
        
        for metric, value in test_results.items():
            if isinstance(value, float):
                click.echo(f"  {metric}: {value:.2f}")
            else:
                click.echo(f"  {metric}: {value}")
    
    # Recommendations
    recommendations = summary.get('recommendations', [])
    if recommendations:
        click.echo(f"\n💡 RECOMMENDATIONS")
        for i, rec in enumerate(recommendations, 1):
            click.echo(f"  {i}. {rec}")
    
    click.echo("\n" + "=" * 60)


if __name__ == '__main__':
    main() 