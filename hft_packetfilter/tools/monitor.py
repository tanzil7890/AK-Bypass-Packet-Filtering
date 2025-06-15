#!/usr/bin/env python3
"""
HFT Monitor - Real-time HFT Network Monitoring CLI Tool

Command-line interface for real-time monitoring of HFT network performance,
latency metrics, and trading infrastructure health.

Author: HFT-PacketFilter Development Team
License: Apache License 2.0
"""

import click
import time
import json
import sys
from typing import Optional, Dict, Any
from datetime import datetime

from ..core.hft_analyzer import HFTAnalyzer
from ..core.exchange_config import ExchangeConfig, CommonExchanges
from ..core.production_config import ProductionConfig
from ..utils.logger import HFTLogger


@click.command()
@click.option('--config', '-c', type=click.Path(exists=True), 
              help='Configuration file path (YAML or JSON)')
@click.option('--exchange', '-e', multiple=True,
              help='Exchange to monitor (can be specified multiple times)')
@click.option('--duration', '-d', type=int, default=0,
              help='Monitoring duration in seconds (0 for indefinite)')
@click.option('--performance-mode', '-p', 
              type=click.Choice(['standard', 'high_performance', 'ultra_low_latency']),
              default='standard', help='Performance mode')
@click.option('--output', '-o', type=click.Choice(['console', 'json', 'csv']),
              default='console', help='Output format')
@click.option('--export-file', type=click.Path(),
              help='Export metrics to file')
@click.option('--refresh-rate', '-r', type=float, default=1.0,
              help='Refresh rate in seconds for console output')
@click.option('--latency-threshold', type=float, default=1000.0,
              help='Latency threshold in microseconds for alerts')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose output')
@click.option('--quiet', '-q', is_flag=True,
              help='Suppress non-essential output')
def main(config: Optional[str], exchange: tuple, duration: int, 
         performance_mode: str, output: str, export_file: Optional[str],
         refresh_rate: float, latency_threshold: float, 
         verbose: bool, quiet: bool):
    """
    HFT Monitor - Real-time High-Frequency Trading Network Monitoring
    
    Monitor HFT network performance, latency metrics, and trading infrastructure
    health in real-time. Supports multiple exchanges and output formats.
    
    Examples:
        hft-monitor --exchange NYSE --exchange NASDAQ
        hft-monitor --config production.yaml --duration 3600
        hft-monitor --performance-mode ultra_low_latency --output json
    """
    
    # Configure logging
    log_level = "DEBUG" if verbose else "WARNING" if quiet else "INFO"
    logger = HFTLogger("hft-monitor", level=log_level)
    
    try:
        # Load configuration
        if config:
            prod_config = ProductionConfig.from_file(config)
        else:
            prod_config = ProductionConfig(performance_mode=performance_mode)
        
        # Initialize analyzer
        analyzer = HFTAnalyzer(
            config=prod_config,
            performance_mode=performance_mode,
            logging_level=log_level
        )
        
        # Add exchanges
        if exchange:
            for exchange_name in exchange:
                if hasattr(CommonExchanges, exchange_name.upper()):
                    exchange_config = getattr(CommonExchanges, exchange_name.upper())()
                    analyzer.add_exchange(exchange_config)
                    logger.info(f"Added exchange: {exchange_name}")
                else:
                    logger.warning(f"Unknown exchange: {exchange_name}")
        else:
            # Add default exchanges if none specified
            analyzer.add_exchange(CommonExchanges.NYSE())
            analyzer.add_exchange(CommonExchanges.NASDAQ())
            logger.info("Added default exchanges: NYSE, NASDAQ")
        
        # Start monitoring
        logger.info(f"Starting HFT monitoring in {performance_mode} mode")
        analyzer.start_monitoring(duration_seconds=duration if duration > 0 else None)
        
        # Monitor and display results
        start_time = time.time()
        
        if output == 'console':
            monitor_console(analyzer, refresh_rate, latency_threshold, duration, start_time, logger)
        elif output == 'json':
            monitor_json(analyzer, refresh_rate, duration, start_time, logger)
        elif output == 'csv':
            monitor_csv(analyzer, refresh_rate, duration, start_time, logger)
        
        # Export results if requested
        if export_file:
            analyzer.export_analysis(export_file, format=export_file.split('.')[-1])
            logger.info(f"Exported results to {export_file}")
        
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Error during monitoring: {e}")
        sys.exit(1)
    finally:
        if 'analyzer' in locals():
            analyzer.stop_monitoring()


def monitor_console(analyzer: HFTAnalyzer, refresh_rate: float, 
                   latency_threshold: float, duration: int, 
                   start_time: float, logger: HFTLogger):
    """Monitor with console output"""
    
    click.echo("=" * 80)
    click.echo("HFT Network Monitor - Real-time Performance Dashboard")
    click.echo("=" * 80)
    click.echo("Press Ctrl+C to stop monitoring\n")
    
    while analyzer.is_monitoring:
        try:
            # Clear screen (works on most terminals)
            click.clear()
            
            # Get current metrics
            metrics = analyzer.get_live_metrics()
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Header
            click.echo("=" * 80)
            click.echo(f"HFT Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo(f"Uptime: {elapsed:.1f}s | Mode: {analyzer.performance_mode}")
            if duration > 0:
                remaining = duration - elapsed
                click.echo(f"Remaining: {remaining:.1f}s")
            click.echo("=" * 80)
            
            # System metrics
            click.echo("\n📊 SYSTEM METRICS")
            click.echo(f"Total Packets: {metrics['trading_metrics']['total_packets']:,}")
            click.echo(f"Monitoring: {'✅ Active' if metrics['is_monitoring'] else '❌ Stopped'}")
            
            # Exchange metrics
            click.echo("\n🏛️  EXCHANGE STATUS")
            for exchange_name, exchange_data in metrics['exchanges'].items():
                status_icon = "🟢" if exchange_data['status'] == 'connected' else "🔴"
                latency = metrics['market_data_quality'].get(exchange_name, {}).get('latency_us', 0)
                quality = metrics['market_data_quality'].get(exchange_name, {}).get('quality_score', 0)
                
                # Check latency threshold
                latency_status = "⚠️" if latency > latency_threshold else "✅"
                
                click.echo(f"{status_icon} {exchange_name:8} | "
                          f"Latency: {latency:6.1f}μs {latency_status} | "
                          f"Quality: {quality:5.1f}% | "
                          f"Target: {exchange_data['latency_target_us']:6.1f}μs")
            
            # Latency statistics
            latency_stats = metrics.get('latency_stats', {})
            if latency_stats:
                click.echo("\n⚡ LATENCY STATISTICS (Last 60s)")
                click.echo(f"Min: {latency_stats.get('min', 0):6.1f}μs | "
                          f"Avg: {latency_stats.get('avg', 0):6.1f}μs | "
                          f"Max: {latency_stats.get('max', 0):6.1f}μs | "
                          f"Count: {latency_stats.get('count', 0):,}")
            
            # Alerts
            alert_stats = metrics.get('alert_stats', {})
            if alert_stats:
                click.echo("\n🚨 ALERTS")
                for alert_type, count in alert_stats.items():
                    if count > 0:
                        click.echo(f"{alert_type}: {count}")
            
            click.echo("\n" + "=" * 80)
            
            # Check if duration exceeded
            if duration > 0 and elapsed >= duration:
                break
            
            time.sleep(refresh_rate)
            
        except KeyboardInterrupt:
            break


def monitor_json(analyzer: HFTAnalyzer, refresh_rate: float, 
                duration: int, start_time: float, logger: HFTLogger):
    """Monitor with JSON output"""
    
    while analyzer.is_monitoring:
        try:
            metrics = analyzer.get_live_metrics()
            
            # Add timestamp and monitoring info
            output = {
                "timestamp": datetime.now().isoformat(),
                "elapsed_seconds": time.time() - start_time,
                "metrics": metrics
            }
            
            click.echo(json.dumps(output, indent=2))
            
            # Check if duration exceeded
            if duration > 0 and (time.time() - start_time) >= duration:
                break
            
            time.sleep(refresh_rate)
            
        except KeyboardInterrupt:
            break


def monitor_csv(analyzer: HFTAnalyzer, refresh_rate: float, 
               duration: int, start_time: float, logger: HFTLogger):
    """Monitor with CSV output"""
    
    # Print CSV header
    click.echo("timestamp,elapsed_seconds,exchange,latency_us,quality_score,status,total_packets")
    
    while analyzer.is_monitoring:
        try:
            metrics = analyzer.get_live_metrics()
            current_time = datetime.now().isoformat()
            elapsed = time.time() - start_time
            
            # Output one row per exchange
            for exchange_name, exchange_data in metrics['exchanges'].items():
                latency = metrics['market_data_quality'].get(exchange_name, {}).get('latency_us', 0)
                quality = metrics['market_data_quality'].get(exchange_name, {}).get('quality_score', 0)
                status = exchange_data['status']
                total_packets = metrics['trading_metrics']['total_packets']
                
                click.echo(f"{current_time},{elapsed:.1f},{exchange_name},"
                          f"{latency:.1f},{quality:.1f},{status},{total_packets}")
            
            # Check if duration exceeded
            if duration > 0 and elapsed >= duration:
                break
            
            time.sleep(refresh_rate)
            
        except KeyboardInterrupt:
            break


if __name__ == '__main__':
    main() 